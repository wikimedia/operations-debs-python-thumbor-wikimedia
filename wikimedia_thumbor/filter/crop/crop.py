#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Crops the image to the specified width and height

from thumbor.filters import BaseFilter, filter_method


class Filter(BaseFilter):

    @filter_method(
        BaseFilter.Number,
        BaseFilter.Number,
        BaseFilter.Number,
        BaseFilter.Number)
    def crop(self, left, top, right, bottom):
        self.engine.realcrop(left, top, right, bottom)
