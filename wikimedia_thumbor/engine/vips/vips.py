#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# VIPS engine

import math
import os
import shutil
from tempfile import mkdtemp

from thumbor.utils import logger

from wikimedia_thumbor.engine import BaseWikimediaEngine
from wikimedia_thumbor.engine import CommandError
from wikimedia_thumbor.shell_runner import ShellRunner  # noqa


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

        if hasattr(self.context, 'wikimedia_original_file'):
            stdout = Engine.exiftool.command(
                pre=command,
                context=self.context,
                input_temp_file=self.context.wikimedia_original_file
            )
        else:
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
            return True  # pragma: no cover
        else:
            if pixels > self.context.config.VIPS_ENGINE_MIN_PIXELS:
                return True

        return False

    def target_format(self):
        if self.context.request.format:
            return '.%s' % self.context.request.format

        return self.context.request.extension

    def create_image(self, buffer):
        # If there is no extension in the request, it means that we
        # are serving a cached result. In which case no VIPS processing
        # is required.
        if not hasattr(self.context.request, 'extension'):
            return super(Engine, self).create_image(buffer)

        self.original_buffer = buffer

        shrink_factor = int(math.floor(
            float(self.context.vips['width'])
            /
            float(self.context.request.width)
        ))

        result = self.shrink(buffer, shrink_factor)

        self.extension = self.target_format()
        logger.debug('[VIPS] Setting extension to: %s' % self.extension)

        return super(Engine, self).create_image(result)

    def shrink(self, buffer, shrink_factor):
        logger.debug('[VIPS] Shrinking with command')
        self.prepare_source(buffer)

        try:
            source = "%s[page=%d]" % (
                self.source,
                self.context.request.page - 1
            )
        except AttributeError:
            source = self.source

        try:
            return self.shrink_for_page(source, shrink_factor)
        except CommandError:
            # The page is probably out of bounds, try again without
            # specifying a page
            source = self.source

        try:
            return self.shrink_for_page(source, shrink_factor)
        except CommandError as e:
            # Now that we've failed twice in a row, we cleanup the source
            self.cleanup_source()
            raise e

    def shrink_for_page(self, source, shrink_factor):
        temp_dir = mkdtemp()
        destination = os.path.join(
            temp_dir,
            'vips_result%s' % self.target_format()
        )

        command = [
            self.context.config.VIPS_PATH,
            'shrink',
            source,
            destination,
            "%d" % shrink_factor,
            "%d" % shrink_factor
        ]

        try:
            self.command(command, clean_on_error=False)
        except CommandError as e:  # pragma: no cover
            ShellRunner.rm_f(destination)
            shutil.rmtree(temp_dir, True)
            raise e

        with open(destination, 'rb') as f:
            result = f.read()

        self.cleanup_source()
        ShellRunner.rm_f(destination)
        shutil.rmtree(temp_dir, True)

        return result
