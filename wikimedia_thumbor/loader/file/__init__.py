#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2018 Wikimedia Foundation

# File loader. Unlike the stock Thumbor one, passes an excerpt
# in the buffer and passes the file location via context, to mimick
# what the other custom loaders do.

from datetime import datetime
from os import fstat
from os.path import join, exists, abspath
from tornado.concurrent import return_future
from tempfile import NamedTemporaryFile
import tornado.simple_httpclient
from functools import partial

from thumbor.loaders import LoaderResult

from wikimedia_thumbor.shell_runner import ShellRunner


def cleanup_temp_file(path):
    ShellRunner.rm_f(path)


@return_future
def load(context, path, callback):
    file_path = join(context.config.FILE_LOADER_ROOT_PATH.rstrip('/'), path.lstrip('/'))
    file_path = abspath(file_path)
    inside_root_path = file_path.startswith(context.config.FILE_LOADER_ROOT_PATH)

    result = LoaderResult()

    if inside_root_path and exists(file_path):

        with open(file_path, 'r') as f:
            stats = fstat(f.fileno())

            result.successful = True
            response = f.read()

            excerpt_length = context.config.LOADER_EXCERPT_LENGTH
            result.buffer = response[:excerpt_length]

            if len(result.buffer) == excerpt_length:
                temp = NamedTemporaryFile(delete=False)
                temp.write(response)
                temp.close()

                context.wikimedia_original_file = temp

                tornado.ioloop.IOLoop.instance().call_later(
                    context.config.HTTP_LOADER_TEMP_FILE_TIMEOUT,
                    partial(
                        cleanup_temp_file,
                        context.wikimedia_original_file.name
                    )
                )

            result.metadata.update(
                size=stats.st_size,
                updated_at=datetime.utcfromtimestamp(stats.st_mtime)
            )
    else:
        result.error = 404
        result.successful = False

    callback(result)
