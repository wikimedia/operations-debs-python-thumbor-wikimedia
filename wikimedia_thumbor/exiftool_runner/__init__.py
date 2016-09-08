#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Utility class to run exiftool commands
#
#
# They can either run as one-off commands or using a long-running
# exiftool process started with the -stay_open option.
#
# Since Thumbor is single-threaded, there is no need for locking
# nor having multiple exiftool processes.


import datetime
import errno
import os
import subprocess
from tempfile import mkdtemp, NamedTemporaryFile

from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner


class ExiftoolRunner:
    process = None
    fifo = None
    fifo_dir = None
    fifo_name = 'exiftool_command_fifo'

    @classmethod
    def start_process(cls, context):
        if cls.process is not None:
            return

        logger.debug(
            '[ExiftoolRunner] start process with -stay_open'
        )

        start = datetime.datetime.now()

        cls.fifo_dir = mkdtemp()
        fifo_name = os.path.join(cls.fifo_dir, cls.fifo_name)
        os.mkfifo(fifo_name)

        command = [
            context.config.EXIFTOOL_PATH,
            '-stay_open',
            'True',
            '-@',
            fifo_name,
        ]

        cls.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        duration = datetime.datetime.now() - start

        cls.add_duration_header(context, duration)

        # We need to wait until exiftool is reading before we
        # open the fifo as write-only. Otherwise open() hangs, waiting
        # for a reader to show up.
        cls.fifo = open(fifo_name, 'w', 0)

        logger.debug('[ExiftoolRunner] process started in %r' % duration)

    @classmethod
    def stay_open_command(cls, preCommand, postCommand, context, buffer):
        start = datetime.datetime.now()

        cls.start_process(context)

        input_fifo_name = os.path.join(cls.fifo_dir, 'exiftool_input_fifo')
        os.mkfifo(input_fifo_name)

        command = preCommand
        command.append(input_fifo_name)
        command += postCommand
        command.append('-execute')

        logger.debug('[ExiftoolRunner] stay_open_command: %r' % command)

        for line in command:
            cls.fifo.write('%s\n' % line)

        input_fifo = open(input_fifo_name, 'w', 0)
        input_fifo.write(buffer)
        input_fifo.close()

        stdout = ''
        line = ''
        marker = '{ready}\n'

        while not line.endswith(marker):
            line = cls.process.stdout.readline()
            if line.endswith(marker):
                stdout += line[:-len(marker)]
            else:
                stdout += line

        try:
            os.remove(input_fifo_name)
        except OSError as e:  # pragma: no cover
            if e.errno != errno.ENOENT:
                raise

        duration = datetime.datetime.now() - start

        cls.add_duration_header(context, duration)

        return stdout

    @classmethod
    def classic_command(cls, preCommand, postCommand, context, buffer):
        start = datetime.datetime.now()

        input_temp_file = NamedTemporaryFile()
        input_temp_file.write(buffer)
        input_temp_file.flush()

        command = [context.config.EXIFTOOL_PATH]
        command += preCommand
        command.append(input_temp_file.name)
        command += postCommand

        logger.debug('[ExiftoolRunner] classic_command: %r' % command)

        code, stderr, stdout = ShellRunner.command(command, context)

        input_temp_file.close()

        duration = datetime.datetime.now() - start

        cls.add_duration_header(context, duration)

        if stderr:
            logger.error('[ExiftoolRunner] error: %r' % stderr)

        return stdout

    @classmethod
    def add_duration_header(cls, context, duration):
        duration = int(round(duration.total_seconds() * 1000, 0))

        context.request_handler.add_header(
            'Exiftool-Time',
            duration
        )

    @classmethod
    def command(cls, pre=[], post=[], context=None, buffer=''):
        try:
            if context.config.EXIFTOOL_STAY_OPEN:
                return cls.stay_open_command(pre, post, context, buffer)
        except AttributeError:  # pragma: no cover
            pass

        return cls.classic_command(pre, post, context, buffer)

    @classmethod
    def cleanup(cls):  # pragma: no cover
        if cls.process:
            logger.debug('[ExiftoolRunner] killing process')
            cls.process.kill()
            cls.process = None

        if cls.fifo:
            logger.debug('[ExiftoolRunner] closing named pipe')
            cls.fifo.close()
            cls.fifo = None

        if cls.fifo_dir:
            if os.path.exists(cls.fifo_dir):
                fifo_name = os.path.join(cls.fifo_dir, cls.fifo_name)
                try:
                    os.remove(fifo_name)
                    os.rmdir(cls.fifo_dir)
                    logger.debug('[ExiftoolRunner] unlinking named pipe')
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise

            cls.fifo_dir = None
