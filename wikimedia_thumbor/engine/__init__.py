#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Base engine, not to be used directly, has to be extended

import shutil
import os

from tempfile import mkdtemp
from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.engine.imagemagick import Engine as IMEngine


class CommandError(Exception):
    pass


class BaseWikimediaEngine(IMEngine):
    # Put temp files and fifos into their own temp folder to avoid
    # exploits where converters might access other files in the same folder
    temp_dir = mkdtemp()

    @classmethod
    def add_format(cls, mime, ext, fn):
        # Unfortunately there is no elegant way to extend Thumbor to support
        # a new MIME type, which is why this monkey-patching is done here
        from thumbor.utils import EXTENSION
        EXTENSION[mime] = ext
        from thumbor.engines import BaseEngine
        old_get_mimetype = BaseEngine.get_mimetype

        @classmethod
        def new_get_mimetype(cls, buffer):
            if fn(buffer):
                return mime

            return old_get_mimetype(buffer)

        BaseEngine.get_mimetype = new_get_mimetype

    def read(self, extension=None, quality=None):
        # read() is sometimes used to read back the original.
        # This relies on the convention that any engine extending
        # BaseWikimediaEngine should set original_buffer inside its
        # create_image method
        if (
            hasattr(self, 'original_buffer') and
            quality is None and
            extension == self.extension
        ):
            logger.debug('[BWE] Reading the original')
            return self.original_buffer

        # When requests don't come through the wikimedia url handler
        # and the format isn't specified, we default to JPG output
        if self.context.request.format is None:
            logger.debug('[BWE] Defaulting to .jpg')
            extension = '.jpg'
        else:
            extension = self.context.request.format
            logger.debug('[BWE] Rendering %s' % extension)

        return super(BaseWikimediaEngine, self).read(extension, quality)

    def prepare_source(self, buffer):
        if hasattr(self.context, 'wikimedia_original_file'):
            logger.debug('[BWE] Found source file in context')
            self.source = self.context.wikimedia_original_file.name
            del self.context.wikimedia_original_file
            return

        logger.debug('[BWE] Create source file from buffer')
        self.source = os.path.join(self.temp_dir, 'source_file')

        with open(self.source, 'w') as source:
            source.write(buffer)

    def cleanup_source(self):
        if hasattr(self, 'source'):
            ShellRunner.rm_f(self.source)

    def cleanup(self):  # pragma: no cover
        shutil.rmtree(self.temp_dir, True)

    def command(self, command, env=None, clean_on_error=True):
        returncode, stderr, stdout = ShellRunner.command(
            command,
            self.context,
            env=env
        )

        if returncode != 0:
            if clean_on_error:
                self.cleanup_source()
            raise CommandError(
                command,
                stdout,
                stderr,
                returncode
            )

        self.cleanup_source()

        return stdout
