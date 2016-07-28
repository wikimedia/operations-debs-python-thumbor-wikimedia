# -*- coding: utf-8 -*-

# Copyright (c) 2015, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from tc_core import Extension, Extensions
from wikimedia_thumbor.extension.purger.handlers.purger import UrlPurgerHandler


extension = Extension('wikimedia_thumbor.extension.purger')

# Register the route
extension.add_handler(UrlPurgerHandler.regex(), UrlPurgerHandler)

Extensions.register(extension)
