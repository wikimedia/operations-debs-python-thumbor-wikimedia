#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# XCF engine

import errno
import os
import time

from wikimedia_thumbor.engine import BaseWikimediaEngine
from wikimedia_thumbor.shell_runner import ShellRunner


BaseWikimediaEngine.add_format(
    'image/xcf',
    '.xcf',
    lambda buffer: buffer.startswith('gimp xcf')
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.original_buffer = buffer
        # xcf2png supports reading from a fifo instead of a file. It can't read
        # from stdin, unfortunately, which is why we settled on the fifo
        fifo = self.prepare_fifo()

        # xcf2png doesn't exist in library form, only as an executable
        command = [
            self.context.config.XCF2PNG_PATH,
            fifo,
            '-o',
            '-'
        ]

        png = self.command_fifo(command, buffer, fifo)

        return super(Engine, self).create_image(png)

    def popen_fifo(self, command, buffer, fifo):
        """
        Writes the buffer contents to the fifo and returns a subprocess for the
        command.
        """
        proc = ShellRunner.popen(
            command,
            self.context
        )

        self.write_buffer_to_fifo(buffer, fifo)

        return proc

    def command_fifo(self, command, buffer, fifo):
        stdout = ''

        proc = self.popen_fifo(command, buffer, fifo)
        stdout, stderr = proc.communicate()

        ShellRunner.rm_f(fifo)

        if proc.returncode != 0:  # pragma: no cover
            raise Exception(
                'CommandError',
                command,
                stdout,
                stderr,
                proc.returncode
            )

        return stdout

    def prepare_fifo(self):
        """
        Creates a fifo and returns its path.
        """
        fifo = os.path.join(self.temp_dir, 'xcf_fifo')
        os.mkfifo(fifo)

        return fifo

    def write_buffer_to_fifo(self, buffer, fifo):
        """
        Writes the contents of the buffer to the fifo.
        """
        while True:
            try:
                os_fifo = os.open(fifo, os.O_NONBLOCK | os.O_WRONLY)
                break
            except OSError as err:
                # We wait until the consumer (xcf2png) starts reading the fifo
                if err.errno == errno.ENXIO:
                    time.sleep(.1)
                    continue
                else:  # pragma: no cover
                    raise

        # The consumer is reading, start writing the buffer contents to the
        # fifo
        seek = 0
        length_written = 0

        while seek == 0 or length_written:
            seek += length_written

            while True:
                try:
                    length_written = os.write(os_fifo, buffer[seek:])
                    break
                except OSError as err:
                    if err.errno == errno.EAGAIN:
                        time.sleep(.1)
                        continue
                    else:  # pragma: no cover
                        os.close(os_fifo)
                        raise

        os.close(os_fifo)
