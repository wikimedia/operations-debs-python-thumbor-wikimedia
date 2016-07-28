#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Proxy engine, redirects requests to other engines
# according to configurable logic

import datetime
import importlib
import resource
from collections import OrderedDict

from thumbor.utils import logger
from thumbor.engines import BaseEngine


def utime():
    return resource.getrusage(resource.RUSAGE_SELF).ru_utime
    + resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime


class Engine(BaseEngine):
    def __init__(self, context):
        engines = OrderedDict(context.config.PROXY_ENGINE_ENGINES)

        # Create an object that will store local values
        # Setting it this way avoids hitting the __setattr__
        # proxying
        super(Engine, self).__setattr__('lcl', {})

        self.lcl['context'] = context
        self.lcl['engines'] = engines

        for engine in engines:
            self.init_engine(context, engine)

    def init_engine(self, context, module):
        mod = importlib.import_module(module)
        klass = getattr(mod, 'Engine')

        self.lcl[module] = klass(context)

    def select_engine(self):
        if self.lcl['selected_engine'] is not None:
            return self.lcl['selected_engine']

        ext = self.lcl['extension'].lstrip('.')

        logger.debug('[Proxy] Looking for a %s engine' % ext)

        for enginename, extensions in self.lcl['engines'].iteritems():
            engine = self.lcl[enginename]

            if ext in extensions:
                if hasattr(engine, 'should_run'):
                    if engine.should_run(self.lcl['buffer']):
                        self.lcl['selected_engine'] = enginename
                        return enginename
                else:
                    self.lcl['selected_engine'] = enginename
                    return enginename

        raise Exception(
            'Unable to find a suitable engine, tried %r' % self.lcl['engines']
        )

    def record_timing(self, timing, header, end):
        duration = end - self.lcl[timing]

        if isinstance(duration, datetime.timedelta):
            duration = duration.total_seconds()

        duration = int(round(duration * 1000, 0))

        self.lcl['context'].metrics.timing(
            'engine.' + timing + '.' + self.select_engine(),
            duration
        )

        self.lcl['context'].request_handler.set_header(
            header,
            duration
        )

    # This is our entry point for the proxy, it's the first call to the engine
    def load(self, buffer, extension):
        self.lcl['processing_time'] = datetime.datetime.now()
        self.lcl['processing_utime'] = utime()

        # buffer and extension are needed by select_engine
        self.lcl['extension'] = extension
        self.lcl['buffer'] = buffer
        self.lcl['selected_engine'] = None

        enginename = self.select_engine()

        # Now that we'll select the right engine, let's initialize it
        self.lcl['context'].request_handler.set_header(
            'Engine',
            enginename
        )

        self.lcl[enginename].__init__(self.lcl['context'])
        self.lcl[enginename].load(buffer, extension)

    def __getattr__(self, name):
        return getattr(self.lcl[self.select_engine()], name)

    def __delattr__(self, name):
        return delattr(self.lcl[self.select_engine()], name)

    def __setattr__(self, name, value):
        return setattr(self.lcl[self.select_engine()], name, value)

    # This is the exit point for requests, where the generated image is
    # converted to the target format
    def read(self, extension=None, quality=None):
        ret = self.__getattr__('read')(extension, quality)

        # The original can be re-read during the request
        if quality is None:
            return ret

        self.record_timing(
            'processing_time',
            'Processing-Time',
            datetime.datetime.now()
        )

        self.record_timing(
            'processing_utime',
            'Processing-Utime',
            utime()
        )

        return ret

    # The following have to be redefined because their fallbacks in BaseEngine
    # don't have the right amount of parameters
    # They call __getattr__ because the calls still need to be proxied
    # (otherwise they would just loop back to their own definition right here)
    def create_image(self, buffer):
        return self.__getattr__('create_image')(buffer)

    def crop(self, left, top, right, bottom):
        return self.__getattr__('crop')(left, top, right, bottom)

    def flip_horizontally(self):
        return self.__getattr__('flip_horizontally')()

    def flip_vertically(self):
        return self.__getattr__('flip_vertically')()

    def image_data_as_rgb(self, update_image=True):
        return self.__getattr__('image_data_as_rgb')(update_image)

    def resize(self, width, height):
        return self.__getattr__('resize')(width, height)

    def rotate(self, degrees):
        return self.__getattr__('rotate')(degrees)

    def reorientate(self):
        return self.__getattr__('reorientate')()

    def set_image_data(self, data):
        return self.__getattr__('set_image_data')(data)

    @property
    def size(self):
        return self.__getattr__('size')

    def cleanup(self):
        # Call cleanup on all the engines
        for enginename, extensions in self.lcl['engines'].iteritems():
            engine = self.lcl[enginename]
            engine.cleanup()
