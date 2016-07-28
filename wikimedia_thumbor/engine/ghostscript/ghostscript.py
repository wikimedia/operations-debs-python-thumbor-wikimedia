#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Ghostscript engine

from wikimedia_thumbor.engine import BaseWikimediaEngine
from wikimedia_thumbor.shell_runner import ShellRunner


BaseWikimediaEngine.add_format(
    'application/pdf',
    '.pdf',
    lambda buffer: buffer.startswith('%PDF')
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.original_buffer = buffer
        self.prepare_source(buffer)

        try:
            page = self.context.request.page
        except AttributeError:
            page = 1

        # We use the command and not the python bindings because those can't
        # use the %stdout option properly. The bindings version writes to
        # stdout forcibly, and that can't be captured with sys.stdout nor the
        # bindings' set_stdio().
        # Using the bindings would therefore force us to use a second temporary
        # file for the destination.
        command = [
            self.context.config.GHOSTSCRIPT_PATH,
            "-sDEVICE=png16m",
            "-sOutputFile=%stdout",
            "-dFirstPage=%d" % page,
            "-dLastPage=%d" % page,
            "-r150",
            "-dBATCH",
            "-dNOPAUSE",
            "-q",
            "-f%s" % self.source
        ]

        png = self.command(command)

        return super(Engine, self).create_image(png)

    def command(self, command, env=None):
        returncode, stderr, stdout = ShellRunner.command(
            command,
            self.context,
            env=env
        )

        if returncode != 0:
            self.cleanup_source()
            raise Exception(
                'CommandError',
                command,
                stdout,
                stderr,
                returncode
            )

        self.cleanup_source()

        return stdout
