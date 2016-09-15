#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# DjVu engine

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/vnd.djvu',
    '.djvu',
    lambda buffer: buffer.startswith('FORM', 4, 8) and
    (
        buffer.startswith('DJVU', 12, 16) or
        buffer.startswith('DJVM', 12, 16) or
        buffer.startswith('PM44', 12, 16) or
        buffer.startswith('BM44', 12, 16)
    )
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.original_buffer = buffer
        self.prepare_source(buffer)

        try:
            page = self.context.request.page
        except AttributeError:
            page = 1

        command = [
            self.context.config.DDJVU_PATH,
            '-format=ppm',
            '-page=%d' % page,
            self.source,
            '-'
        ]

        ppm = self.command(command)

        return super(Engine, self).create_image(ppm)
