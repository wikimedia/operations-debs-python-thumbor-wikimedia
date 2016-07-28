#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# This is a fork of the thumbor.filters.sharpen filter
# This version only applies the sharpening if the thumbnail resize
# ratio is smaller than the resize ratio threshold passed as the
# last parameter

from thumbor.filters import BaseFilter, filter_method
from thumbor.ext.filters import _sharpen


class Filter(BaseFilter):

    @filter_method(
        BaseFilter.DecimalNumber,
        BaseFilter.DecimalNumber,
        BaseFilter.Boolean,
        BaseFilter.DecimalNumber
    )
    def conditional_sharpen(
            self,
            amount,
            radius,
            luminance_only,
            resize_ratio_threshold):

        width, height = self.engine.size
        try:
            original_width = self.context.request.source_width
        except AttributeError:
            original_width = self.engine.source_width

        try:
            original_height = self.context.request.source_height
        except AttributeError:
            original_height = self.engine.source_height

        mode, data = self.engine.image_data_as_rgb()
        source_sum = float(original_width + original_height)
        destination_sum = float(width + height)
        resize_ratio = destination_sum / source_sum

        if resize_ratio < resize_ratio_threshold:
            imgdata = _sharpen.apply(
                mode, width, height, amount, radius,
                luminance_only, data
            )
            self.engine.set_image_data(imgdata)
