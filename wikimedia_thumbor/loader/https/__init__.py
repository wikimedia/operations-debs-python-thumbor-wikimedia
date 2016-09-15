#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Https loader. Unlike the stock Thumbor one, uses a streaming callback
# and can define a higher body size limit than 100MB

from functools import partial
from tempfile import NamedTemporaryFile
import tornado.simple_httpclient


from thumbor.loaders import http_loader, https_loader
from thumbor.utils import logger


def should_run(url):  # pragma: no cover
    return True


def return_contents(response, url, callback, context, f):  # pragma: no cover
    # We put the first kb of content into the response body, to let Thumbor's
    # mime detection work
    f.seek(0)
    response._body = f.read(1024)
    context.wikimedia_original_file = f
    f.close()
    return http_loader.return_contents(response, url, callback, context)


def stream_contents(response, f):
    f.write(response)


def load_sync(context, url, callback):
    logger.debug('[HTTPS] load_sync: %s' % url)
    client = tornado.simple_httpclient.SimpleAsyncHTTPClient(
        max_clients=context.config.HTTP_LOADER_MAX_CLIENTS,
        max_body_size=context.config.HTTP_LOADER_MAX_BODY_SIZE
    )

    user_agent = None
    if context.config.HTTP_LOADER_FORWARD_USER_AGENT:
        if 'User-Agent' in context.request_handler.request.headers:
            user_agent = context.request_handler.request.headers['User-Agent']
    if user_agent is None:
        user_agent = context.config.HTTP_LOADER_DEFAULT_USER_AGENT

    f = NamedTemporaryFile(delete=False)

    url = https_loader._normalize_url(url)
    req = tornado.httpclient.HTTPRequest(
        url=url,
        connect_timeout=context.config.HTTP_LOADER_CONNECT_TIMEOUT,
        request_timeout=context.config.HTTP_LOADER_REQUEST_TIMEOUT,
        follow_redirects=context.config.HTTP_LOADER_FOLLOW_REDIRECTS,
        max_redirects=context.config.HTTP_LOADER_MAX_REDIRECTS,
        user_agent=user_agent,
        proxy_host=encode(context.config.HTTP_LOADER_PROXY_HOST),
        proxy_port=context.config.HTTP_LOADER_PROXY_PORT,
        proxy_username=encode(context.config.HTTP_LOADER_PROXY_USERNAME),
        proxy_password=encode(context.config.HTTP_LOADER_PROXY_PASSWORD),
        ca_certs=encode(context.config.HTTP_LOADER_CA_CERTS),
        client_key=encode(context.config.HTTP_LOADER_CLIENT_KEY),
        client_cert=encode(context.config.HTTP_LOADER_CLIENT_CERT),
        streaming_callback=partial(stream_contents, f=f)
    )

    client.fetch(
        req, callback=partial(
            return_contents,
            url=url,
            callback=callback,
            context=context,
            f=f
        )
    )


def encode(string):
    return None if string is None else string.encode('ascii')
