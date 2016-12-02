# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler allows to use the built-in thumbor
# handler with an appropriate URL prefix

import re
from libthumbor.url import Url
import tornado.gen as gen

from thumbor.handlers.imaging import ImagingHandler


class CoreHandler(ImagingHandler):
    @classmethod
    def regex(cls):
        return r'/thumbor/(?P<request>.*)'

    @gen.coroutine
    def check_image(self, kw):
        result = re.match(Url.regex(), kw['request'])
        return super(CoreHandler, self).check_image(result.groupdict())
