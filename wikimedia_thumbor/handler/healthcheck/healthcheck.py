# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler allows to use the built-in thumbor healthcheck
# handler within the context of our custom app


from thumbor.handlers.healthcheck import HealthcheckHandler as BaseHandler


class HealthcheckHandler(BaseHandler):
    @classmethod
    def regex(cls):
        return r'/healthcheck'
