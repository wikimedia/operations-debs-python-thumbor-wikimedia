#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Proxy loader, redirects requests to other loaders
# according to configurable logic

import importlib

from thumbor.loaders import http_loader, https_loader
from tornado.concurrent import return_future
from thumbor.utils import logger


modules = {}


def _normalize_url(url):
    return https_loader._normalize_url(url)


def validate(context, url):
    return http_loader.validate(
        context,
        url,
        normalize_url_func=_normalize_url
    )


def return_contents(response, url, callback, context):  # pragma: no cover
    return http_loader.return_contents(response, url, callback, context)


def encode(string):  # pragma: no cover
    return http_loader.encode(string)


@return_future
def load(context, url, callback):
    for loader in context.config.PROXY_LOADER_LOADERS:
        if loader in modules:
            mod = modules[loader]
        else:
            logger.debug('Importing: %s' % loader)
            mod = importlib.import_module(loader)
            modules[loader] = mod

        if mod.should_run(url):
            return mod.load_sync(context, url, callback)

    return http_loader.load_sync(
        context,
        url,
        callback,
        normalize_url_func=_normalize_url
    )
