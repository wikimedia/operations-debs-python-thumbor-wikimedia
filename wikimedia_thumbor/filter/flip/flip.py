#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Flips the image horizontally or vertically

from thumbor.filters import BaseFilter, filter_method


class Filter(BaseFilter):

    @filter_method(BaseFilter.String)
    def flip(self, value):
        if value == 'x':
            self.engine.flip_vertically()
        elif value == 'y':
            self.engine.flip_horizontally()
