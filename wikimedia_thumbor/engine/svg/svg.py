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
import StringIO

from thumbor.utils import logger

from wikimedia_thumbor.engine import BaseWikimediaEngine


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.original_buffer = buffer

        if hasattr(self.context.config, 'RSVG_CONVERT_PATH'):
            logger.debug('[SVG] Converting with rsvg')
            png = self.create_image_with_rsvg(buffer)
        else:
            logger.debug('[SVG] Converting with cairosvg')
            png = self.create_image_with_cairosvg(buffer)

        return super(Engine, self).create_image(png)

    def create_image_with_cairosvg(self, buffer):
        cairosvg.features.LOCALE = 'en_US'

        if hasattr(self.context.request, 'lang'):
            request_locale = self.context.request.lang.upper()
            normalized_locale = locale.normalize(request_locale)
            cairosvg.features.LOCALE = normalized_locale

        output = StringIO.StringIO()

        return cairosvg.svg2png(
            bytestring=buffer,
            dpi=self.context.config.SVG_DPI
        )

    def create_image_with_rsvg(self, buffer):
        self.prepare_source(buffer)

        command = [
            self.context.config.RSVG_CONVERT_PATH,
            self.source,
            '-f',
            'png'
        ]

        if self.context.request.width > 0:
            command += ['-w', '%d' % self.context.request.width]

        if self.context.request.height > 0:  # pragma: no cover
            command += ['-h', '%d' % self.context.request.height]

        env = None
        if hasattr(self.context.request, 'lang'):
            env = {'LANG': self.context.request.lang.upper()}

        return self.command(command, env)

    # Disable this method in BaseEngine, do the conversion in create_image
    # instead
    def convert_svg_to_png(self, buffer):
        return buffer
