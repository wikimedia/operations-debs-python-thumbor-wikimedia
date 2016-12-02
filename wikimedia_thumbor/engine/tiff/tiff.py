#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# TIFF engine

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/tiff',
    '.tiff',
    lambda buffer: buffer.startswith('II*\x00') or buffer.startswith('MM\x00*')
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        img = super(Engine, self).create_image(buffer)

        try:
            page = self.context.request.page

            if page <= len(img.sequence):
                for i in range(0, page - 1):
                    # Remove any page before the one we want
                    del(img.sequence[0])
        except AttributeError:
            pass

        # Remove any page after the one we want
        while len(img.sequence) > 1:
            del(img.sequence[1])

        return img
