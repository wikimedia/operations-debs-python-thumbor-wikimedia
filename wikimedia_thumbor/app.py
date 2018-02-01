#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 Wikimedia Foundation

import manhole
import os.path
import tempfile

import thumbor.engines

from thumbor.utils import logger, which

from thumbor.handlers import ContextHandler
from tc_core import Extensions
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

        # T178072 Disable Thumbor's built-in EXIF parsing, which
        # emits logger.error messages constantly because it's trying
        # to parse our truncated buffer. EXIF parsing is done in our
        # imagemagick engine instead.
        thumbor.engines.METADATA_AVAILABLE = False

        super(App, self).__init__(context)

    # We override this to avoid the catch-all ImagingHandler from
    # Thumbor which prevents us from 404ing properly on completely
    # broken URLs.
    def get_handlers(self):
        '''Return a list of tornado web handlers.
        '''

        handlers = []

        for extensions in Extensions.extensions:
            for handler in extensions.handlers:

                # Inject the context if the handler expects it.
                if issubclass(handler[1], ContextHandler):
                    if len(handler) < 3:
                        handler = list(handler)
                        handler.append(dict(context=self.context))
                    else:
                        handler[2]['context'] = self.context

                handlers.append(handler)

        return handlers
