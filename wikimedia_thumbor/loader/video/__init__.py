#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Video loader, only loads the frame needed from a remote video
# Do not use it as-is with persistent storage of originals,
# otherwise the first frame requested will be stored as the
# original for subsequent requests

import errno
import re
import os
from functools import partial
from tempfile import NamedTemporaryFile

from thumbor.loaders import LoaderResult
from thumbor.utils import logger

from tornado.concurrent import return_future
from tornado.process import Subprocess


from wikimedia_thumbor.shell_runner import ShellRunner


def should_run(url):  # pragma: no cover
    normalized_url = _normalize_url(url).lower()

    if (normalized_url.endswith('.ogv') or
            normalized_url.endswith('.ogg') or
            normalized_url.endswith('.webm')):
        return True

    return False


@return_future
def load(context, url, callback):
    return load_sync(context, url, callback)


def load_sync(context, url, callback):
    # Disable storage of original. These lines are useful if
    # you want your Thumbor instance to store all originals persistently
    # except video frames.
    #
    # from thumbor.storages.no_storage import Storage as NoStorage
    # context.modules.storage = NoStorage(context)

    normalized_url = _normalize_url(url)

    command = ShellRunner.wrap_command([
        context.config.FFPROBE_PATH,
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        '%s' % normalized_url
    ], context)

    logger.debug('[Video] load_sync: %r' % command)

    process = Subprocess(
        command,
        stdout=Subprocess.STREAM,
        stderr=Subprocess.STREAM
    )

    process.set_exit_callback(
        partial(
            _parse_time_status,
            context,
            normalized_url,
            callback,
            process
        )
    )


def _http_code_from_stderr(process, result, normalized_url):
    result.successful = False
    stderr = process.stderr.read_from_fd()

    logger.error('[Video] Fprobe/ffmpeg errored: %r normalized_url: %r' % (stderr, normalized_url))
    code = re.match('.*Server returned (\d\d\d).*', stderr)

    if code:
        code = int(code.group(1))

    if code == 404:
        result.error = LoaderResult.ERROR_NOT_FOUND
    elif code == 599:
        result.error = LoaderResult.ERROR_TIMEOUT
    elif code == 500:
        result.error = LoaderResult.ERROR_UPSTREAM


def _parse_time_status(context, normalized_url, callback, process, status):
    if status != 0:
        result = LoaderResult()

        _http_code_from_stderr(process, result, normalized_url)
        process.stdout.close()
        process.stderr.close()

        callback(result)
    else:
        process.stdout.read_until_close(
            partial(
                _parse_time,
                context,
                normalized_url,
                callback
            )
        )

        process.stdout.close()
        process.stderr.close()


def _parse_time(context, normalized_url, callback, output):
    # T183907 Some files have completely corrupt duration fields,
    # but we can still extract their first frame for a thumbnail
    try:
        duration = float(output)
    except ValueError:
        duration = 0.0

    try:
        seek = int(context.request.page)
    except AttributeError:
        seek = duration / 2

    seek_and_screenshot(callback, context, normalized_url, seek)


def seek_and_screenshot(callback, context, normalized_url, seek):
    output_file = NamedTemporaryFile(delete=False)

    command = ShellRunner.wrap_command([
        context.config.FFMPEG_PATH,
        # Order is important, for fast seeking -ss has to come before -i
        # As explained on https://trac.ffmpeg.org/wiki/Seeking
        '-ss',
        '%d' % seek,
        '-i',
        '%s' % normalized_url,
        '-y',
        '-vframes',
        '1',
        '-an',
        '-f',
        'image2',
        '-nostats',
        '-loglevel',
        'fatal',
        output_file.name
    ], context)

    logger.debug('[Video] _parse_time: %r' % command)

    process = Subprocess(
        command,
        stdout=Subprocess.STREAM,
        stderr=Subprocess.STREAM
    )

    process.set_exit_callback(
        partial(
            _process_done,
            callback,
            process,
            context,
            normalized_url,
            seek,
            output_file
        )
    )


def _process_done(
        callback,
        process,
        context,
        normalized_url,
        seek,
        output_file,
        status
        ):
    # T183907 Sometimes ffmpeg returns status 0 and actually fails to
    # generate a thumbnail. We double-check the existence of the thumbnail
    # in case of apparent success
    if status == 0:
        if os.stat(output_file.name).st_size == 0:
            status = -1

    # If rendering the desired frame fails, attempt to render the
    # first frame instead
    if status != 0 and seek > 0:
        seek_and_screenshot(callback, context, normalized_url, 0)
        return

    result = LoaderResult()

    if status != 0:  # pragma: no cover
        _http_code_from_stderr(process, result, normalized_url)
    else:
        result.successful = True
        result.buffer = output_file.read()

    process.stdout.close()
    process.stderr.close()

    output_file.close()

    try:
        os.unlink(output_file.name)
    except OSError as e:  # pragma: no cover
        if e.errno != errno.ENOENT:
            logger.error('[Video] Unable to unlink output file')
            raise

    callback(result)


def _normalize_url(url):
    # URLs provided by Thumbor to load() are fully URL-escaped, including the protocol.
    # We unescape just the colon of the protocol to get a valid and properly escaped URL.
    rewritten_parts = []
    parts = url.split('/')

    for part in parts[:-1]:
        rewritten_parts.append(re.sub(r'%3A', r':', part))

    rewritten_parts.append(parts[-1])

    return '/'.join(rewritten_parts)
