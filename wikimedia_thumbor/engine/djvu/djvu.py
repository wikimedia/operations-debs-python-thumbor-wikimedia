#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# DjVu engine

# Otherwise Python thinks that djvu is the local module
from __future__ import absolute_import

import djvu.decode

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/vnd.djvu',
    '.djvu',
    lambda buffer: buffer.startswith('FORM', 4, 8) and
    (
        buffer.startswith('DJVU', 12, 16) or
        buffer.startswith('DJVM', 12, 16) or
        buffer.startswith('PM44', 12, 16) or
        buffer.startswith('BM44', 12, 16)
    )
)


class Engine(BaseWikimediaEngine):
    pixel_format = djvu.decode.PixelFormatRgb('RGB')
    pixel_format.rows_top_to_bottom = 1
    pixel_format.y_top_to_bottom = 1

    def create_image(self, buffer):
        self.original_buffer = buffer
        # Unfortunately the djvu python bindings don't support reading
        # file contents from memory, nor from a fifo. Which means we have to
        # store the input in a temporary file
        self.prepare_source(buffer)

        try:
            page = self.context.request.page - 1
        except AttributeError:
            page = 0

        context = djvu.decode.Context()
        file_uri = djvu.decode.FileURI(self.source)
        document = context.new_document(file_uri, cache=False)
        document.decoding_job.wait()

        # If we try to read a page out of bounds, use the first page
        if page < 0 or page > len(document.pages) - 1:
            page = 0

        document_page = document.pages[page]
        page_job = document_page.decode(wait=True)

        width, height = page_job.size
        rect = (0, 0, width, height)

        data = page_job.render(
            djvu.decode.RENDER_COLOR,
            rect,
            rect,
            self.pixel_format
        )

        # PBM is a very simple file format, which ImageMagick can consume
        ppm = 'P6 %d %d 255\n' % (width, height)
        ppm += data

        self.cleanup_source()

        return super(Engine, self).create_image(ppm)
