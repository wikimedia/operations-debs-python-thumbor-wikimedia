#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# VIPS engine

import logging
import math
import os

from thumbor.utils import logger

from wikimedia_thumbor.engine import BaseWikimediaEngine
from wikimedia_thumbor.engine import CommandError
from wikimedia_thumbor.shell_runner import ShellRunner  # noqa


use_command_line = True

try:
    import gi
    if hasattr(gi, 'require_version'):
        logger.debug('[VIPS] gi found')
        try:
            gi.require_version('Vips', '8.0')
            logging.disable(logging.DEBUG)
            from gi.repository import Vips
            logging.disable(logging.NOTSET)
            logger.debug('[VIPS] VIPS found in gi repository')
            use_command_line = False
        except ImportError:
            logger.debug('[VIPS] VIPS not found in gi repository')
        except ValueError:
            logger.debug('[VIPS] VIPS 8.0+ not found in gi repository')
    else:
        logger.debug('[VIPS] Wrong gi found (not PyGObject)')
except ImportError:
    logger.debug('[VIPS] gi not found')

if use_command_line:
    logger.debug('[VIPS] Will use command line')
else:
    logger.debug('[VIPS] Will use bindings')

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

        shrink_factor = int(math.floor(
            float(self.context.vips['width'])
            /
            float(self.context.request.width)
        ))

        if use_command_line:
            result = self.shrink_with_command(buffer, shrink_factor)
        else:
            result = self.shrink_with_bindings(buffer, shrink_factor)

        self.extension = original_ext

        return super(Engine, self).create_image(result)

    def shrink_with_bindings(self, buffer, shrink_factor):
        logger.debug('[VIPS] Shrinking with bindings')
        logging.disable(logging.DEBUG)

        if gi and hasattr(gi, 'overrides'):
            exceptions = (AttributeError, gi.overrides.Vips.Error)
        else:
            exceptions = AttributeError

        try:
            page = self.context.request.page - 1
            source = Vips.Image.new_from_buffer(buffer, 'page=%d' % page)
        except exceptions:
            source = Vips.Image.new_from_buffer(buffer, '')

        source = source.shrink(shrink_factor, shrink_factor)
        result = source.write_to_buffer('.png')

        logging.disable(logging.NOTSET)
        return result

    def shrink_with_command(self, buffer, shrink_factor):
        logger.debug('[VIPS] Shrinking with command')
        self.prepare_source(buffer)

        try:
            source = "%s[page=%d]" % (
                self.source,
                self.context.request.page - 1
            )
        except AttributeError:
            source = self.source

        destination = os.path.join(self.temp_dir, 'vips_result.png')

        command = [
            self.context.config.VIPS_PATH,
            'shrink',
            source,
            destination,
            "%d" % shrink_factor,
            "%d" % shrink_factor
        ]

        try:
            self.command(command)
        except CommandError as e:
            ShellRunner.rm_f(destination)
            raise e

        with open(destination, 'rb') as f:
            result = f.read()

        self.cleanup_source()
        ShellRunner.rm_f(destination)

        return result
