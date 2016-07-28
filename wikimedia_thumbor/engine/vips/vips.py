#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# VIPS engine

import gi
import logging
import math

if hasattr(gi, 'require_version'):
    pgi = gi
else:
    import pgi

pgi.require_version('Vips', '8.0')

# VIPS is very chatty in the debug logs
logging.disable(logging.DEBUG)
from pgi.repository import Vips
logging.disable(logging.NOTSET)

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/tiff',
    '.tiff',
    lambda buffer: (
        buffer.startswith('II*\x00') or buffer.startswith('MM\x00*')
    )
)


class Engine(BaseWikimediaEngine):
    def should_run(self, buffer):
        self.context.vips = {}

        command = [
            '-ImageSize',
            '-s',
            '-s',
            '-s'
        ]

        stdout = Engine.exiftool.command(
            pre=command,
            context=self.context,
            buffer=buffer
        )

        size = stdout.strip().split('x')

        self.context.vips['width'] = int(size[0])
        self.context.vips['height'] = int(size[1])

        pixels = self.context.vips['width'] * self.context.vips['height']

        if self.context.config.VIPS_ENGINE_MIN_PIXELS is None:
            return True
        else:
            if pixels > self.context.config.VIPS_ENGINE_MIN_PIXELS:
                return True

        return False

    def create_image(self, buffer):
        try:
            original_ext = self.context.request.extension
        except AttributeError:
            # If there is no extension in the request, it means that we
            # are serving a cached result. In which case no VIPS processing
            # is required.
            return super(Engine, self).create_image(buffer)

        self.original_buffer = buffer

        # VIPS is very chatty in the debug logs
        logging.disable(logging.DEBUG)

        try:
            page = self.context.request.page - 1
            source = Vips.Image.new_from_buffer(buffer, 'page=%d' % page)
        except AttributeError, gi.overrides.Vips.Error:
            source = Vips.Image.new_from_buffer(buffer, '')

        shrink_factor = int(math.floor(
            float(self.context.vips['width'])
            /
            float(self.context.request.width)
        ))

        source = source.shrink(shrink_factor, shrink_factor)
        result = source.write_to_buffer('.png')

        logging.disable(logging.NOTSET)

        self.extension = original_ext

        return super(Engine, self).create_image(result)
