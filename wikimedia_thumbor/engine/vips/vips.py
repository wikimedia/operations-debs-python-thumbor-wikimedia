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

    def create_image(self, buffer):
        # If there is no extension in the request, it means that we
        # are serving a cached result. In which case no VIPS processing
        # is required.
        if not hasattr(self.context.request, 'extension'):
            return super(Engine, self).create_image(buffer)

        # We shrink to roughly twice the size we need, then the rest of the resizing is done
        # by Imagemagick. We can't resize straight to the size we need since the shrink factor
        # in this version of VIPS is an integer
        shrink_factor = max(1, int(math.floor(
            float(self.context.vips['width'])
            /
            (2.0 * float(self.context.request.width))
        )))

        # T218272: If shrink_factor == 1, VIPS doesn't scale the image.
        # Don't bother running the command and just let ImageMagick handle it.
        if shrink_factor == 1:
            return super(Engine, self).create_image(buffer)

        result = self.shrink(buffer, shrink_factor)

        return super(Engine, self).create_image(result)

    def shrink(self, buffer, shrink_factor):
        self.debug('[VIPS] Shrinking with command')
        self.prepare_source(buffer)

        try:
            source = "%s[page=%d]" % (
                self.source,
                self.context.request.page - 1
            )
        except AttributeError:
            source = self.source

        output_args = ""

        for i in range(3):
            try:
                return self.shrink_for_page(source, shrink_factor, output_args)
            except CommandError as e:
                if "does not contain page" in e.args[2]:
                    # The page is probably out of bounds, try again without
                    # specifying a page
                    source = self.source
                elif "profile" in e.args[2] and "vips2png: unable to write" in e.args[2]:
                    # libpng doesn't want to write files with ICC profiles
                    # that it doesn't like. Force those images to use TinyRGB
                    self.debug('[VIPS] Forcing TinyRGB profile')
                    output_args = "[profile=%s]" % self.context.config.EXIF_TINYRGB_PATH
                elif i >= 1:
                    # Tried at least twice, but failed and we're out of ideas
                    self.cleanup_source()
                    raise e

    def shrink_for_page(self, source, shrink_factor, output_args=""):
        temp_dir = mkdtemp()
        destination = os.path.join(
            temp_dir,
            'vips_result.png'
        )

        command = [
            self.context.config.VIPS_PATH,
            'shrink',
            source,
            destination + output_args,
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
