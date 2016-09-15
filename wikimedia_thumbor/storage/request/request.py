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
        return path

    @return_future
    def exists(self, path, callback):
        callback(path in self.dict)

    @return_future
    def get(self, path, callback):
        logger.debug("[REQUEST_STORAGE] get: %s" % path)
        try:
            value = self.dict[path]
            logger.debug("[REQUEST_STORAGE] found")
            callback(value)
        except KeyError:
            logger.debug("[REQUEST_STORAGE] missing")
            callback(None)
