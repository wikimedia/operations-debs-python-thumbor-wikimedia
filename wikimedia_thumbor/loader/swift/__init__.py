#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Swift loader. Streams objects from Swift with auth

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


swiftconn = None


def should_run(url):  # pragma: no cover
    return True


def cleanup_temp_file(path):
    logger.debug('[SWIFT_LOADER] cleanup_temp_file: %s' % path)
    ShellRunner.rm_f(path)


def swift(context):
    global swiftconn

    if swiftconn:
        return swiftconn

    authurl = (
        context.config.SWIFT_HOST +
        context.config.SWIFT_AUTH_PATH
    )

    swiftconn = client.Connection(
        user=context.config.SWIFT_USER,
        key=context.config.SWIFT_KEY,
        authurl=authurl,
        timeout=context.config.SWIFT_CONNECTION_TIMEOUT,
        retries=context.config.SWIFT_RETRIES
    )

    return swiftconn


def load_sync(context, url, callback):
    logger.debug('[SWIFT_LOADER] load_sync: %s' % url)

    result = LoaderResult()

    container = context.wikimedia_original_container
    path = context.wikimedia_original_filepath

    try:
        logger.debug(
            '[SWIFT_LOADER] fetching %s from container %s' % (path, container)
        )
        logging.disable(logging.ERROR)
        headers, response = swift(context).get_object(
            container,
            path,
            resp_chunk_size=context.config.HTTP_LOADER_MAX_BODY_SIZE
        )

        context.metrics.incr('swift_loader.status.success')

        logging.disable(logging.NOTSET)

        f = NamedTemporaryFile(delete=False)
        for chunk in response:
            logger.debug(
                '[SWIFT_LOADER] writing %d bytes to temp file' % len(chunk)
            )
            f.write(chunk)

        excerpt_length = context.config.LOADER_EXCERPT_LENGTH

        f.seek(0)
        # First kb of the body for MIME detection
        body = f.read(excerpt_length)
        f.close()

        if len(body) == excerpt_length:
            logger.debug('[SWIFT_LOADER] return_contents: %s' % f.name)
            context.wikimedia_original_file = f

            tornado.ioloop.IOLoop.instance().call_later(
                context.config.HTTP_LOADER_TEMP_FILE_TIMEOUT,
                partial(
                    cleanup_temp_file,
                    context.wikimedia_original_file.name
                )
            )
        else:
            logger.debug('[SWIFT_LOADER] return_contents: small body')
            cleanup_temp_file(f.name)

        result.buffer = body
    except ClientException as e:
        logging.disable(logging.NOTSET)
        result.successful = False
        result.error = LoaderResult.ERROR_NOT_FOUND
        logger.error('[SWIFT_LOADER] get_object failed: %s %r' % (url, e))
        context.metrics.incr('swift_loader.status.client_exception')
    except requests.ConnectionError as e:
        logging.disable(logging.NOTSET)
        result.successful = False
        result.error = LoaderResult.ERROR_UPSTREAM
        logger.error('[SWIFT_LOADER] get_object failed: %s %r' % (url, e))
        context.metrics.incr('swift_loader.status.connection_error')

    callback(result)
