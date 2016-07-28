#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Utility class to run shell commands safely

import datetime
import errno
import os
import subprocess

from thumbor.utils import logger


class ShellRunner:
    @classmethod
    def wrap_command(cls, command, context):
        wrapped_command = command

        try:
            cgroup = context.config.SUBPROCESS_CGROUP
            cgexec_path = context.config.SUBPROCESS_CGEXEC_PATH
            wrapped_command = [
                cgexec_path,
                '-g',
                cgroup
            ] + wrapped_command
        except AttributeError:
            pass

        try:
            timeout = context.config.SUBPROCESS_TIMEOUT
            timeout_path = context.config.SUBPROCESS_TIMEOUT_PATH
            wrapped_command = [
                timeout_path,
                '--foreground',
                '%s' % timeout
            ] + wrapped_command
        except AttributeError:
            pass

        return wrapped_command

    @classmethod
    def popen(cls, command, context, stdin=None, env=None):
        wrapped_command = ShellRunner.wrap_command(
            command,
            context
        )

        logger.debug('[ShellRunner] Command: %r' % wrapped_command)

        combined_env = os.environ.copy()

        if env is not None:
            combined_env.update(env)

        if stdin is None:
            proc = subprocess.Popen(
                wrapped_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=combined_env
            )
        else:
            proc = subprocess.Popen(
                wrapped_command,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=combined_env
            )
            proc.stdin.write(stdin)

        return proc

    @classmethod
    def command(cls, command, context, stdin=None, env=None):
        start = datetime.datetime.now()

        proc = cls.popen(command, context, stdin, env)

        stdout, stderr = proc.communicate()

        duration = datetime.datetime.now() - start
        duration = duration.total_seconds() * 1000

        length = len(stdout)

        if length > 1000:
            logger.debug('Stdout: <too long to display (%d bytes)>' % length)
        else:
            logger.debug('Stdout: %s' % stdout)

        logger.debug('Stderr: %s' % stderr)
        logger.debug('Return code: %d' % proc.returncode)
        logger.debug('Duration: %r' % duration)

        return proc.returncode, stderr, stdout

    @classmethod
    def rm_f(cls, path):
        """Remove a file if it exists."""
        try:
            os.unlink(path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
