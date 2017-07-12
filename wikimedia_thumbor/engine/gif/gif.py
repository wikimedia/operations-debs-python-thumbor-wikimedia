#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# GIF engine
# This makes GIF handling compatible with the wikimedia https loader
# Actual processing is handled by the Thumbor built-in gifsicle-based engine

from thumbor.engines.gif import Engine as BaseEngine
from wikimedia_thumbor.engine import BaseWikimediaEngine
from wikimedia_thumbor.shell_runner import ShellRunner

BaseWikimediaEngine.add_format(
    'image/gif',
    '.gif',
    lambda buffer: Engine.is_gif(buffer)
)


class Engine(BaseEngine):
    @classmethod
    def is_gif(cls, buffer):
        return buffer.startswith('GIF8')

    def resize(self, width, height):
        super(Engine, self).resize(width, height)
        # Allow Gifsicle to add intermediate colors when resizing images.
        # Normally, Gifsicle’s resize algorithms use input images’ color
        # palettes without changes. When shrinking images with very few colors
        # (e.g., pure black-and-white images), adding intermediate colors can
        # improve the results. The following option allows Gifsicle to add
        # intermediate colors for images that have fewer than 64 input colors.
        self.operations.append("--resize-colors 64")

    def load(self, buffer, extension):
        if hasattr(self.context, 'wikimedia_original_file'):
            fname = self.context.wikimedia_original_file.name
            with open(fname, 'r') as content_file:
                buffer = content_file.read()
            ShellRunner.rm_f(fname)

        return super(Engine, self).load(buffer, extension)
