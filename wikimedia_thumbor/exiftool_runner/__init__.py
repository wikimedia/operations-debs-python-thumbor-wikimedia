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
from tempfile import NamedTemporaryFile

from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner


class ExiftoolRunner:
    @classmethod
    def command(
        cls,
        pre=[],
        post=[],
        context=None,
        buffer='',
        input_temp_file=None
    ):
        start = datetime.datetime.now()

        if not input_temp_file:
            input_temp_file = NamedTemporaryFile()
            input_temp_file.write(buffer)
            input_temp_file.flush()

        command = [context.config.EXIFTOOL_PATH]
        command += pre
        command.append(input_temp_file.name)
        command += post

        logger.debug('[ExiftoolRunner] command: %r' % command)

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
