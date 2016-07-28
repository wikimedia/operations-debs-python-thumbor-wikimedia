#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 Wikimedia Foundation
#
# Simply stores originals in a local dictionary
# In practice this deliberately shouldn't work
# across requests, unless the same instance of this class
# is passed between requests (which is the case for /multi)

from tornado.concurrent import return_future

from thumbor.storages import BaseStorage
from thumbor.utils import logger


class Storage(BaseStorage):
    def __init__(self, context):
        BaseStorage.__init__(self, context)
        self.dict = {}

    def put(self, path, contents):
        logger.debug("[REQUEST_STORAGE] put: %s" % path)
        self.dict[path] = contents
        return path

    def put_crypto(self, path):
        if not self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
            return

        if not self.context.server.security_key:
            raise RuntimeError(
                "STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True"
                + " if no SECURITY_KEY specified"
            )

        return path

    @return_future
    def exists(self, path, callback):
        callback(path in self.dict)

    @return_future
    def get(self, path, callback):
        logger.debug("[REQUEST_STORAGE] get: %s" % path)
        try:
            logger.debug("[REQUEST_STORAGE] found")
            callback(self.dict[path])
        except KeyError:
            logger.debug("[REQUEST_STORAGE] missing")
            callback(None)
