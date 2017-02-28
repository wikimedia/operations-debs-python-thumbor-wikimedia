#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# TIFF engine

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/tiff',
    '.tiff',
    lambda buffer: buffer.startswith('II*\x00') or buffer.startswith('MM\x00*')
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        return super(Engine, self).create_image(buffer)
