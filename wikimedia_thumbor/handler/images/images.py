# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler translates mediawiki thumbnail urls into thumbor urls
# And sets the xkey for Varnish purging purposes

from urllib import quote
import json
import md5
import tornado.gen as gen

from thumbor.context import RequestParameters
from thumbor.handlers import BaseHandler
from thumbor.handlers.imaging import ImagingHandler
from thumbor.utils import logger


BaseHandler._old_error = BaseHandler._error


# We need to monkey-patch BaseHandler because otherwise we
# wouldn't apply the Cache-Control headers to 400 errors that
# don't make it to ImagesHandler since they don't match the
# handlers' regexp.
def _error(self, status, msg=None):
    # Errors should explicitely not be cached
    self.set_header(
        'Cache-Control',
        'no-cache'
    )
    self.clear_header('xkey')
    self.clear_header('Content-Disposition')
    self.clear_header('Wikimedia-Original-Container')
    self.clear_header('Wikimedia-Thumbnail-Container')
    self.clear_header('Wikimedia-Original-Path')
    self.clear_header('Wikimedia-Thumbnail-Path')
    self.clear_header('Thumbor-Parameters')
    BaseHandler._old_error(self, status, msg)


BaseHandler._error = _error


class TranslateError(Exception):
    pass


class ImagesHandler(ImagingHandler):
    @classmethod
    def regex(cls):
        return (
            r'/'
            r'(?P<project>[^-/]+)/'
            r'(?P<language>[^/]+)/'
            r'thumb/'
            r'(?:(?P<specialpath>temp|archive)/)?'
            r'(?P<shard1>[0-9a-zA-Z]+)/'
            r'(?P<shard2>[0-9a-zA-Z]+)/'
            r'(?P<filename>[^/]+)\.'
            r'(?P<extension>[^/]+)/'
            r'(?:(?P<qlow>qlow-))?'
            r'(?:(?P<lossy>lossy-))?'
            r'(?:(?P<lossless>lossless-))?'
            r'(?:page(?P<page>\d+)-)?'
            r'(?:lang(?P<lang>[a-zA-Z]+)-)?'
            r'(?P<width>\d+)px-'
            r'(?:seek=(?P<seek>\d+)-)?'
            r'(?P<end>[^/]+)'
            r'\.(?P<format>[a-zA-Z]+)'
        )

    def generate_save_swift_path(self, kw):
        path = '/'.join(
            (
                kw['shard1'],
                kw['shard2'],
                kw['filename'] + '.' + kw['extension'],
                ''
            )
        )

        if kw['specialpath']:
            # This is done for backwards compatibility. I assume that the reasoning
            # was that since the  temp thumbnails are stored alongside the originals
            # in the temp container, changing the prefix made things clearer when
            # inspecting the contents of the container.
            if kw['specialpath'] == 'temp':
                kw['specialpath'] = 'thumb'
            path = '/'.join((kw['specialpath'], path))

        if kw['qlow'] == 'qlow-':
            path += kw['qlow']

        if kw['lossy'] == 'lossy-':  # pragma: no cover
            path += kw['lossy']

        if kw['lossless'] == 'lossless-':
            path += kw['lossless']

        if kw['page']:
            path += 'page' + kw['page'] + '-'

        if kw['lang']:
            path += 'lang' + kw['lang'] + '-'

        path += kw['width'] + 'px-'

        if kw['seek']:
            path += 'seek=' + kw['seek'] + '-'

        path += kw['end']

        path += '.' + kw['format']

        return path

    def translate(self, kw):
        logger.debug('[ImagesHandler] translate: %r' % kw)

        translated = {'width': kw['width']}

        if int(kw['width']) < 1:
            raise TranslateError('Width requested must be at least 1')

        sharded_containers = []

        if hasattr(self.context.config, 'SWIFT_SHARDED_CONTAINERS'):
            sharded_containers = self.context.config.SWIFT_SHARDED_CONTAINERS

        projlang = '-'.join((kw['project'], kw['language']))
        original_container = projlang + '-local-public'
        thumbnail_container = projlang + '-local-thumb'
        original_shard1 = kw['shard1']
        original_shard2 = kw['shard2']
        thumbnail_shard2 = kw['shard2']

        # Temp is different from any other case. Originals are thumbnails are
        # stored alongside each other in the same container. The hash prefix
        # is different for thumbnails and originals. Thumbnails stick to the
        # standard hash prefix scheme. While the hash prefix used for originals
        # is recalculated by excluding the date and exclamation point the filename
        # contains.
        # This twisted logic is reproduced here for backwards compatibility.
        if kw['specialpath'] == 'temp':
            original_container = projlang + '-local-temp'
            thumbnail_container = projlang + '-local-temp'
            filename = kw['filename']

            if '!' in filename:
                hashed_name = filename.split('!', 1)[1] + '.' + kw['extension']
                hashed = md5.new(hashed_name).hexdigest()
                original_shard1 = hashed[:1]
                original_shard2 = hashed[:2]

        if original_container in sharded_containers:
            original_container += '.' + original_shard2

        if thumbnail_container in sharded_containers:
            thumbnail_container += '.' + thumbnail_shard2

        original_filepath = '/'.join(
            (
                original_shard1,
                original_shard2,
                kw['filename'] + '.' + kw['extension']
            )
        )

        # Temp originals are not prefixed by the specialpath.
        # I assume that the logic was that within the context of the temp
        # containers, everything is a temp file and there's no need to prefix
        # storage paths.
        # Except of course for thumbnails... see generate_save_swift_path
        # for that case.
        if kw['specialpath'] and kw['specialpath'] != 'temp':
            original_filepath = '/'.join(
                (kw['specialpath'], original_filepath)
            )

        swift_original_uri = (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_API_PATH +
            original_container
        )

        swift_original_uri += '/'

        translated['image'] = swift_original_uri + original_filepath

        filters = []

        if kw['format'].lower() in ('jpe', 'jpeg'):
            kw['format'] = 'jpg'

        if kw['extension'].lower() in ('jpg', 'jpe', 'jpeg'):
            if (
                kw['qlow'] == 'qlow-' and
                hasattr(self.context.config, 'QUALITY_LOW')
            ):
                logger.debug('[ImagesHandler] apply JPG low quality')
                filters.append('quality(%d)' % self.context.config.QUALITY_LOW)

            if hasattr(self.context.config, 'DEFAULT_FILTERS_JPEG'):
                logger.debug('[ImagesHandler] apply JPG default filters')
                filters.append(self.context.config.DEFAULT_FILTERS_JPEG)

        filters.append('format(%s)' % kw['format'])

        page = kw.get('page')

        if not page:
            page = kw.get('seek')

        if page:
            filters.append('page(%s)' % page)

        lang = kw.get('lang')

        if lang:
            filters.append('lang(%s)' % lang)

        if filters:
            translated['filters'] = ':'.join(filters)

        self.context.wikimedia_original_container = original_container
        self.context.wikimedia_original_filepath = original_filepath
        self.context.wikimedia_thumbnail_container = thumbnail_container
        self.context.wikimedia_thumbnail_save_path = \
            self.generate_save_swift_path(kw)

        if hasattr(self.context.config, 'SWIFT_PATH_PREFIX'):
            self.context.wikimedia_thumbnail_save_path = (
                self.context.config.SWIFT_PATH_PREFIX +
                self.context.wikimedia_thumbnail_save_path
            )

        return translated

    def safe_set_header(self, header, value):
        try:
            self.set_header(header, value)
        except ValueError as e:
            logger.debug('[ImagesHandler] Skip setting invalid header: %r', e)

    def set_headers(self, translated):
        original_filepath = self.context.wikimedia_original_filepath
        original_filename = original_filepath.rsplit('/', 1)[1]
        original_extension = original_filename.rsplit('.', 1)[1]
        thumbnail_filepath = self.context.wikimedia_thumbnail_save_path
        thumbnail_extension = thumbnail_filepath.rsplit('.', 1)[1]

        self.safe_set_header(
            'xkey',
            u'File:' + original_filename
        )

        content_disposition = original_filename
        if thumbnail_extension != original_extension:
            content_disposition += '.' + thumbnail_extension

        self.safe_set_header(
            'Content-Disposition',
            u'inline;filename*=UTF-8\'\'%s' % content_disposition
        )

        self.safe_set_header(
            'Wikimedia-Original-Container',
            self.context.wikimedia_original_container
        )

        self.safe_set_header(
            'Wikimedia-Thumbnail-Container',
            self.context.wikimedia_thumbnail_container
        )

        self.safe_set_header(
            'Wikimedia-Original-Path',
            self.context.wikimedia_original_filepath
        )

        self.safe_set_header(
            'Wikimedia-Thumbnail-Path',
            self.context.wikimedia_thumbnail_save_path
        )

        self.safe_set_header(
            'Thumbor-Parameters',
            json.dumps(translated)
        )

    @gen.coroutine
    def check_image(self, kw):
        try:
            translated_kw = self.translate(kw)
        except TranslateError as e:
            self._error(
                400,
                str(e)
            )
            return

        self.set_headers(translated_kw)

        if self.context.config.MAX_ID_LENGTH > 0:
            # Check if an image with an uuid exists in storage
            image = translated_kw['image']
            truncated_image = image[:self.context.config.MAX_ID_LENGTH]
            maybe_future = self.context.modules.storage.exists(truncated_image)
            exists = yield gen.maybe_future(maybe_future)
            if exists:  # pragma: no cover
                translated_kw['image'] = truncated_image

        translated_kw['image'] = quote(translated_kw['image'].encode('utf-8'))
        if not self.validate(translated_kw['image']):  # pragma: no cover
            self._error(
                400,
                'No original image was specified in the given URL'
            )
            return

        translated_kw['request'] = self.request
        self.context.request = RequestParameters(**translated_kw)

        self.execute_image_operations()
