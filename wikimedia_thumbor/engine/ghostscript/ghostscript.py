#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Ghostscript engine

from wikimedia_thumbor.engine import BaseWikimediaEngine, CommandError
from wikimedia_thumbor.shell_runner import ShellRunner


BaseWikimediaEngine.add_format(
    "application/pdf",
    ".pdf",
    lambda buffer: buffer.startswith("%PDF")
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        try:
            page = self.context.request.page
        except AttributeError:
            page = 1

        self.prepare_source(buffer)

        jpg, stderr = self.get_jpg_for_page(buffer, page)

        # GS is being unhelpful and outputting that error to stderr
        # with a 0 exit status
        error = "No pages will be processed (FirstPage > LastPage)"
        if len(jpg) < 200 and stderr.find(error) != -1:
            jpg, stderr = self.get_jpg_for_page(buffer, 1)

        self.cleanup_source()

        self.extension = ".jpg"

        return super(Engine, self).create_image(jpg)

    def get_jpg_for_page(self, buffer, page):
        # We use the command and not the python bindings because those can't
        # use the %stdout option properly. The bindings version writes to
        # stdout forcibly, and that can't be captured with sys.stdout nor the
        # bindings' set_stdio().
        # Using the bindings would therefore force us to use a second temporary
        # file for the destination.
        command = [
            self.context.config.GHOSTSCRIPT_PATH,
            "-sDEVICE=jpeg",
            "-dJPEG=90",
            "-sstdout=%stderr",
            "-sOutputFile=%stdout",
            "-dFirstPage=%d" % page,
            "-dLastPage=%d" % page,
            "-r150",
            "-dBATCH",
            "-dNOPAUSE",
            "-dSAFER",
            "-q",
            "-f%s" % self.source,
        ]

        returncode, stderr, stdout = ShellRunner.command(command, self.context)
        if returncode != 0:
            raise CommandError(command, stdout, stderr, returncode)

        return stdout, stderr
