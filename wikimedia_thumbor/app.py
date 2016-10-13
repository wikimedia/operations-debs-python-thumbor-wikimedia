#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 Wikimedia Foundation

import manhole
import os.path
import tempfile

from thumbor.utils import logger, which

from tc_core.app import App as CommunityCoreApp


class App(CommunityCoreApp):
    def __init__(self, context):
        if context.config.get('MANHOLE_DEBUGGING', None):
            logger.debug('Installing manhole')
            socket = 'manhole-%s' % context.server.port
            socket_path = os.path.join(
                tempfile.gettempdir(),
                socket
            )

            manhole.install(socket_path=socket_path)

        # The gifsicle engine needs to work, regardless of
        # USE_GIFSICLE_ENGINE being on or not
        context.server.gifsicle_path = which('gifsicle')

        super(App, self).__init__(context)
