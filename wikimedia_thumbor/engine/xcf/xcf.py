#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# XCF engine

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/xcf',
    '.xcf',
    lambda buffer: buffer.startswith('gimp xcf')
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.original_buffer = buffer
        self.prepare_source(buffer)

        # xcf2png doesn't exist in library form, only as an executable
        command = [
            self.context.config.XCF2PNG_PATH,
            self.source,
            '-o',
            '-'
        ]

        png = self.command(command)
        self.extension = '.png '

        return super(Engine, self).create_image(png)
