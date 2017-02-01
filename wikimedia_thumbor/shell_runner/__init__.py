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
from functools import partial
import os
import subprocess

from thumbor.utils import logger


class ShellRunner:
    @classmethod
    def wrap_command(cls, command, context):
        wrapped_command = command

        if getattr(context.config, 'SUBPROCESS_USE_TIMEOUT', False):
            timeout = context.config.SUBPROCESS_TIMEOUT
            timeout_path = context.config.SUBPROCESS_TIMEOUT_PATH
            wrapped_command = [
                timeout_path,
                '--foreground',
                '%s' % timeout
            ] + wrapped_command

        return wrapped_command

    @classmethod
    def preexec(cls, context):  # pragma: no cover
        if not getattr(context.config, 'SUBPROCESS_CGROUP_TASKS_PATH', False):
            return

        pid = os.getpid()

        logger.debug('[ShellRunner] Adding pid %r to cgroup' % pid)

        with open(context.config.SUBPROCESS_CGROUP_TASKS_PATH, 'a+') as tasks:
            tasks.write('%s\n' % pid)

    @classmethod
    def popen(cls, command, context, env=None):
        wrapped_command = ShellRunner.wrap_command(
            command,
            context
        )

        logger.debug('[ShellRunner] Command: %r' % wrapped_command)

        combined_env = os.environ.copy()

        if env is not None:  # pragma: no cover
            combined_env.update(env)

        proc = subprocess.Popen(
            wrapped_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=combined_env,
            preexec_fn=partial(cls.preexec, context)
        )

        return proc

    @classmethod
    def command(cls, command, context, env=None):
        start = datetime.datetime.now()

        proc = cls.popen(command, context, env)

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
        except OSError as e:  # pragma: no cover
            if e.errno != errno.ENOENT:
                raise
