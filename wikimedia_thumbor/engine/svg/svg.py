#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# SVG engine

import cairosvg
import locale

from bs4 import BeautifulSoup

from wikimedia_thumbor.engine import BaseWikimediaEngine

BaseWikimediaEngine.add_format(
    'image/svg+xml',
    '.svg',
    lambda buffer: Engine.is_svg(buffer)
)


class Engine(BaseWikimediaEngine):
    @classmethod
    def is_svg(cls, buffer):
        soup = BeautifulSoup(buffer, 'xml')

        return soup.svg is not None

    def create_image(self, buffer):
        self.original_buffer = buffer

        cairosvg.features.LOCALE = 'en_US'

        if hasattr(self.context.request, 'lang'):
            request_locale = self.context.request.lang.upper()
            normalized_locale = locale.normalize(request_locale)
            cairosvg.features.LOCALE = normalized_locale

        png = cairosvg.svg2png(
            bytestring=buffer,
            dpi=self.context.config.SVG_DPI
        )

        return super(Engine, self).create_image(png)

    # Disable this method in BaseEngine, do the conversion in create_image
    # instead
    def convert_svg_to_png(self, buffer):
        return buffer
