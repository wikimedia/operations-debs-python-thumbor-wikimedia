#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# SVG engine

from wikimedia_thumbor.engine import BaseWikimediaEngine

BaseWikimediaEngine.add_format(
    'image/svg+xml',
    '.svg',
    lambda buffer: Engine.is_svg(buffer)
)


class Engine(BaseWikimediaEngine):
    @classmethod
    def is_svg(cls, buffer):
        # Quite wide, but it's better to let rsvg give a file a shot
        # rather than bail without trying
        return (buffer.startswith('<?xml') and
                'http://www.w3.org/2000/svg' in buffer)

    def create_image(self, buffer):
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

        png = self.command(command, env)

        return super(Engine, self).create_image(png)

    # Disable this method in BaseEngine, do the conversion in create_image
    # instead
    def convert_svg_to_png(self, buffer):
        return buffer
