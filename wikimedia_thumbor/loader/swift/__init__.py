#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Swift loader. Streams objects from Swift with auth

import datetime
import logging
import requests
from functools import partial
from tempfile import NamedTemporaryFile
from swiftclient import client
from swiftclient.exceptions import ClientException
import tornado.simple_httpclient


from thumbor.loaders import LoaderResult
from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.logging import record_timing, log_extra


swiftconn = None
swiftconn_private = None


def should_run(url):  # pragma: no cover
    return True


def cleanup_temp_file(context, path):
    logger.debug('[SWIFT_LOADER] cleanup_temp_file: %s' % path, extra=log_extra(context))
    ShellRunner.rm_f(path)


def swift(context):
    global swiftconn, swiftconn_private

    if context.private:
        if swiftconn_private:
            return swiftconn_private
    else:
        if swiftconn:
            return swiftconn

    authurl = (
        context.config.SWIFT_HOST +
        context.config.SWIFT_AUTH_PATH
    )

    # This allows us to set the value via config, instead of depending on the
    # x-storage-url header returned by Swift during auth. This is a requirement
    # for communicating with Swift via HTTPS.
    os_options = {
        'object_storage_url': context.config.SWIFT_HOST + context.config.SWIFT_API_PATH
    }

    conn = client.Connection(
        user=context.config.SWIFT_PRIVATE_USER if context.private else context.config.SWIFT_USER,
        key=context.config.SWIFT_PRIVATE_KEY if context.private else context.config.SWIFT_KEY,
        authurl=authurl,
        timeout=context.config.SWIFT_CONNECTION_TIMEOUT,
        retries=context.config.SWIFT_RETRIES,
        os_options=os_options
    )

    if context.private:
        swiftconn_private = conn
    else:
        swiftconn = conn

    return conn


def load_sync(context, url, callback):
    logger.debug('[SWIFT_LOADER] load_sync: %s' % url, extra=log_extra(context))

    result = LoaderResult()

    container = context.wikimedia_original_container
    path = context.wikimedia_original_filepath

    try:
        logger.debug(
            '[SWIFT_LOADER] fetching %s from container %s' % (path, container),
            extra=log_extra(context)
        )

        start = datetime.datetime.now()

        logging.disable(logging.ERROR)
        headers, response = swift(context).get_object(
            container,
            path
        )
        logging.disable(logging.NOTSET)

        record_timing(context, datetime.datetime.now() - start, 'swift.original.read.success', 'Thumbor-Swift-Original-Success-Time')

        context.metrics.incr('swift_loader.status.success')

        # XXX hack: If the file is an STL, we overwrite the first five bytes
        # with the word "solid", to trick the MIME detection pipeline.
        extension = path[-4:].lower()
        isSTL = extension == '.stl'

        f = NamedTemporaryFile(delete=False)
        logger.debug(
            '[SWIFT_LOADER] writing %d bytes to temp file' % len(response),
            extra=log_extra(context)
        )
        f.write(response)
        f.close()

        excerpt_length = context.config.LOADER_EXCERPT_LENGTH

        # First kb of the body for MIME detection
        body = response[:excerpt_length]

        # See above - text STLs have this string here anyway, and
        # binary STLs ignore the first 80 bytes, so this string will
        # be ignored.
        if isSTL:
            body = 'solid' + body[5:]

        if len(body) == excerpt_length:
            logger.debug('[SWIFT_LOADER] return_contents: %s' % f.name, extra=log_extra(context))
            context.wikimedia_original_file = f

            tornado.ioloop.IOLoop.instance().call_later(
                context.config.HTTP_LOADER_TEMP_FILE_TIMEOUT,
                partial(
                    cleanup_temp_file,
                    context,
                    context.wikimedia_original_file.name
                )
            )
        else:
            logger.debug('[SWIFT_LOADER] return_contents: small body')
            cleanup_temp_file(context, f.name)

        result.buffer = body
    except ClientException as e:
        record_timing(context, datetime.datetime.now() - start, 'swift.original.read.miss', 'Thumbor-Swift-Original-Miss-Time')
        logging.disable(logging.NOTSET)
        result.successful = False
        result.error = LoaderResult.ERROR_NOT_FOUND
        logger.error('[SWIFT_LOADER] get_object failed: %s %r' % (url, e), extra=log_extra(context))
        context.metrics.incr('swift_loader.status.client_exception')
    except requests.ConnectionError as e:
        record_timing(context, datetime.datetime.now() - start, 'swift.original.read.exception', 'Thumbor-Swift-Original-Exception-Time')
        logging.disable(logging.NOTSET)
        result.successful = False
        result.error = LoaderResult.ERROR_UPSTREAM
        logger.error('[SWIFT_LOADER] get_object failed: %s %r' % (url, e), extra=log_extra(context))
        context.metrics.incr('swift_loader.status.connection_error')

    callback(result)
