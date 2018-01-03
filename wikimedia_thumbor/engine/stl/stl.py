#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2017 Wikimedia Foundation

# STL engine

import struct
import os
import tempfile
from io import BytesIO

from wikimedia_thumbor.engine import BaseWikimediaEngine
from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.engine import CommandError

BaseWikimediaEngine.add_format(
    'application/sla',
    '.stl',
    lambda buffer: Engine.is_stl(buffer)
)


class Engine(BaseWikimediaEngine):
    @classmethod
    def is_stl(cls, buffer):
        # This is pretty much impossible to know for sure,
        # but I guess we'll give it a
        try:
            stream = BytesIO(buffer)
            start = stream.read(5)

            # The only consistent thing in text STL files is the string
            # 'solid' at the beginning, so if that's there, assume we have
            # a valid ASCII STL.
            # Also, any files served from Wikimedia's Swift loader will have
            # this string at the beginning for sure. Hacky, but it works.
            if start == 'solid':
                return True

            # Now we either have a non-STL, or we have a binary STL file.
            # There is literally no consistent way to tell whether a binary
            # file is actually an STL file, but the header is 80 bytes...
            stream.read(75)

            # ...and then there's 4 bytes that indicate how many triangles are
            # present in the file...
            triangles = stream.read(4)
            triangles = struct.unpack("<L", triangles)[0]

            # ...so there should be exactly that number, times 386 (the number
            # of bytes in each triangle), left in the file...
            remainder = stream.read(triangles * 386)

            # ...so if we got at east that many bytes...
            if len(remainder) == triangles * 386:
                # ...and there aren't any extras...
                extra = stream.read1(1)
                if len(extra) == 0:
                    # ...this is as close to a golden STL file check as we're
                    # going to get.
                    return True
        except IndexError:
            pass

        return False

    def create_image(self, buffer):
        self.prepare_source(buffer)

        height = round(self.context.request.width / (640. / 480.))

        tmpfile, tmppng = tempfile.mkstemp(suffix='.stl.png', prefix='tmpthumb')

        # We don't need the file actually, just the filename
        os.close(tmpfile)

        command = [
            self.context.config.XVFB_RUN_PATH,
            '-a',
            '-n',
            str(os.getpid()),
            '-s',
            '-ac -screen 0 1280x1024x24',
            self.context.config.THREED2PNG_PATH,
            self.source,
            '%dx%d' % (self.context.request.width, height),
            tmppng
        ]

        try:
            self.command(command)
        except CommandError as e:
            ShellRunner.rm_f(tmppng)
            raise e

        tmpfile = open(tmppng, 'rb')
        png = tmpfile.read()
        tmpfile.close()
        ShellRunner.rm_f(tmppng)

        return super(Engine, self).create_image(png)
