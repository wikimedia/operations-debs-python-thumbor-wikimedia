# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler lets one warm up caches by generating a list of requested
# thumbnails asynchronously.

import re

import tornado.web
from tornado import gen
from tornado.httputil import HTTPServerRequest

from thumbor.handlers.imaging import ImagingHandler
from libthumbor.url import Url


class MultiHandler(ImagingHandler):
    paths_limit = 128

    @classmethod
    def regex(cls):
        return r'/multi'

    @tornado.web.asynchronous
    @gen.coroutine
    def post(self, **kw):
        paths = self.get_arguments('paths[]')

        if len(paths) > MultiHandler.paths_limit:
            self.set_status(400)
            super(MultiHandler, self).write(
                'Too many paths: %d max' % MultiHandler.paths_limit
            )
            super(MultiHandler, self).finish()
            return

        for path in paths:
            request = HTTPServerRequest(
                method='GET',
                uri=path,
                host=self.request.host,
                connection=self.request.connection
            )

            handler = MultiHandler(
                self.application,
                request,
                context=self.context
            )

            # Copy over the storage as-is, which allows those requests to
            # share storage if needed (useful for request-storage)
            handler.context.modules.storage = self.context.modules.storage

            m = re.match(Url.regex(), path)
            yield handler.check_image(m.groupdict())

        # Close the request ASAP, the work is to be done async
        self.set_status(200)
        super(MultiHandler, self).finish()

    # We don't want /multi to serve any of the requested content
    def write(self, chunk):
        pass

    def finish(self, chunk=None):
        pass

    def add_header(self, name, value):
        pass

    def set_header(self, name, value):
        pass
