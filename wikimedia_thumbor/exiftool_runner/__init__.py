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


from tempfile import NamedTemporaryFile

from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.logging import log_extra


class ExiftoolRunner:
    @classmethod
    def command(
        cls,
        context,
        pre=[],
        post=[],
        buffer='',
        input_temp_file=None
    ):
        if not input_temp_file:
            input_temp_file = NamedTemporaryFile()
            input_temp_file.write(buffer)
            input_temp_file.flush()

        command = [context.config.EXIFTOOL_PATH]
        command += pre
        command.append(input_temp_file.name)
        command += post

        logger.debug('[ExiftoolRunner] command: %r' % command, extra=log_extra(context))

        code, stderr, stdout = ShellRunner.command(command, context)

        input_temp_file.close()

        if stderr:
            logger.error('[ExiftoolRunner] error: %r' % stderr, extra=log_extra(context))

        return stdout
