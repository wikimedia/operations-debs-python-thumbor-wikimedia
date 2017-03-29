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
    swiftconn = None

    @property
    def swift(self):
        if Storage.swiftconn:
            return Storage.swiftconn

        authurl = (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_AUTH_PATH
        )

        # This allows us to set the value via config, instead of depending on the
        # x-storage-url header returned by Swift during auth. This is a requirement
        # for communicating with Swift via HTTPS.
        os_options = {
            'object_storage_url': self.context.config.SWIFT_HOST + self.context.config.SWIFT_API_PATH
        }

        Storage.swiftconn = client.Connection(
            user=self.context.config.SWIFT_USER,
            key=self.context.config.SWIFT_KEY,
            authurl=authurl,
            timeout=self.context.config.SWIFT_CONNECTION_TIMEOUT,
            retries=self.context.config.SWIFT_RETRIES,
            os_options=os_options
        )

        return Storage.swiftconn

    def uri(self):  # pragma: no cover
        return (
            self.context.config.SWIFT_HOST +
            self.context.wikimedia_thumbnail_container +
            '/' +
            self.context.wikimedia_thumbnail_save_path
        )

    # Coverage strangely reports lines lacking coverage in that function that
    # don't make sense
    def put(self, bytes):  # pragma: no cover
        self.debug('[SWIFT_STORAGE] put')

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
                self.context.wikimedia_thumbnail_save_path,
                bytes,
                headers=headers
            )

            # We cannot set the time spent in putting to swift in the response
            # headers, because the response has already been sent when saving
            # to Swift happens (which is the right thing to do).
        except Exception as e:
            self.error('[SWIFT_STORAGE] put exception: %r' % e)
            # We cannnot let exceptions bubble up, because they would leave
            # the client's connection hanging

    @return_future
    def get(self, callback):
        self.debug('[SWIFT_STORAGE] get: %r %r' % (
                self.context.wikimedia_thumbnail_container,
                self.context.wikimedia_thumbnail_save_path
            )
        )

        try:
            start = datetime.datetime.now()

            # swiftclient has this annoying habit of writing an ERROR log
            # entry for the ClientException, regardless of it being caught
            logging.disable(logging.ERROR)
            headers, data = self.swift.get_object(
                self.context.wikimedia_thumbnail_container,
                self.context.wikimedia_thumbnail_save_path
            )
            logging.disable(logging.NOTSET)

            duration = datetime.datetime.now() - start
            duration = int(round(duration.total_seconds() * 1000))

            self.context.request_handler.add_header(
                'Swift-Time', duration
            )

            self.debug('[SWIFT_STORAGE] found')
            callback(data)
        # We want this to be exhaustive because not catching an exception here
        # would result in the request hanging indefinitely
        except ClientException:
            logging.disable(logging.NOTSET)
            # No need to log this one, it's expected behavior when the
            # requested object isn't there
            self.debug('[SWIFT_STORAGE] missing')
            callback(None)
        except Exception as e:
            logging.disable(logging.NOTSET)
            self.error('[SWIFT_STORAGE] get exception: %r' % e)
            callback(None)

    def debug(self, message):
        logger.debug(message, extra={'url': self.context.request.url})

    def error(self, message):
        logger.error(message, extra={'url': self.context.request.url})
