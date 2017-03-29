#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2017 Wikimedia Foundation

# PoolCounter client

import socket

import tornado.gen as gen
import tornado.iostream

from thumbor.utils import logger


class PoolCounter:
    def __init__(self, context):
        self.server = context.config.POOLCOUNTER_SERVER
        self.port = context.config.get('POOLCOUNTER_PORT', 7531)
        self.context = context
        self.stream = None

    @gen.coroutine
    def connect(self):
        self.debug('[PoolCounter] Connecting to: %s %d' % (self.server, self.port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = tornado.iostream.IOStream(s)
        yield self.stream.connect((self.server, self.port))

    @gen.coroutine
    def acq4me(self, key, workers, maxqueue, timeout):
        if not self.stream:
            self.connect()

        try:
            self.debug('[PoolCounter] ACQ4ME %s %d %d %d' % (key, workers, maxqueue, timeout))
            yield self.stream.write('ACQ4ME %s %d %d %d\n' % (key, workers, maxqueue, timeout))
            data = yield self.stream.read_until('\n')
        except socket.error as e:
            self.stream = None
            raise e

        raise tornado.gen.Return(data == 'LOCKED\n')

    @gen.coroutine
    def release(self):
        if not self.stream:
            self.connect()

        try:
            self.debug('[PoolCounter] RELEASE')
            yield self.stream.write('RELEASE\n')
            data = yield self.stream.read_until('\n')
        except socket.error as e:
            self.stream = None
            raise e

        raise tornado.gen.Return(data == 'RELEASED\n')

    def close(self):
        if self.stream:
            self.debug('[PoolCounter] Disconnecting')
            self.stream.close()
            self.stream = None
            return True
        else:
            self.debug('[PoolCounter] Already disconnected')
            return False

    def debug(self, message):
        logger.debug(message, extra={'url': self.context.request.url})
