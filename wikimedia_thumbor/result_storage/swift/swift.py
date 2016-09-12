#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 Wikimedia Foundation
#
# Stores results in Swift via HTTP

import datetime
import logging

from swiftclient import client
from swiftclient.exceptions import ClientException
from tornado.concurrent import return_future

from thumbor.result_storages import BaseStorage
from thumbor.utils import logger


class Storage(BaseStorage):
    def __init__(self, context):
        super(Storage, self).__init__(context)

        authurl = (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_AUTH_PATH
        )

        # Doesn't actually connect, this happens lazily on the first
        # get_object or put_object call
        self.swift = client.Connection(
            user=self.context.config.SWIFT_USER,
            key=self.context.config.SWIFT_KEY,
            authurl=authurl,
            timeout=self.context.config.SWIFT_CONNECTION_TIMEOUT,
            retries=self.context.config.SWIFT_RETRIES
        )

    def uri(self):  # pragma: no cover
        return (
            self.context.config.SWIFT_HOST +
            self.context.wikimedia_thumbnail_container +
            '/' +
            self.context.wikimedia_path
        )

    # Coverage strangely reports lines lacking coverage in that function that
    # don't make sense
    def put(self, bytes):  # pragma: no cover
        logger.debug('[Swift] put')

        if not hasattr(self.context, 'wikimedia_thumbnail_container'):
            return

        try:
            # We store the xkey alongside the object if it's set.
            # This way when an thumbnail falls our of Varnish and is picked
            # up from Swift again, it will have an xkey. Which lets us avoid
            # computing the xkey in Varnish. It always comes from Thumbor.
            headers = None
            xkey = self.context.request_handler._headers.get_list('xkey')

            if len(xkey):
                headers = {'xkey': xkey[0]}

            self.swift.put_object(
                self.context.wikimedia_thumbnail_container,
                self.context.wikimedia_path,
                bytes,
                headers=headers
            )

            # We cannot set the time spent in putting to swift in the response
            # headers, because the response has already been sent when saving
            # to Swift happens (which is the right thing to do).
        except Exception as e:
            logger.error('[Swift] put exception: %r' % e)
            # We cannnot let exceptions bubble up, because they would leave
            # the client's connection hanging

    @return_future
    def get(self, callback):
        logger.debug('[Swift] get')

        try:
            start = datetime.datetime.now()

            # swiftclient has this annoying habit of writing an ERROR log
            # entry for the ClientException, regardless of it being caught
            logging.disable(logging.ERROR)
            headers, data = self.swift.get_object(
                self.context.wikimedia_thumbnail_container,
                self.context.wikimedia_path
            )
            logging.disable(logging.NOTSET)

            duration = datetime.datetime.now() - start
            duration = int(round(duration.total_seconds() * 1000))

            self.context.request_handler.add_header(
                'Swift-Time', duration
            )

            callback(data)
        # We want this to be exhaustive because not catching an exception here
        # would result in the request hanging indefinitely
        except ClientException:
            logging.disable(logging.NOTSET)
            # No need to log this one, it's expected behavior when the
            # requested object isn't there
            callback(None)
        except Exception as e:
            logging.disable(logging.NOTSET)
            logger.error('[Swift] get exception: %r' % e)
            callback(None)
