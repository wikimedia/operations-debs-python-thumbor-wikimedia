# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler translates mediawiki thumbnail urls into thumbor urls
# And sets the xkey for Varnish purging purposes

import tornado.web

from thumbor.handlers.imaging import ImagingHandler


class ImagesHandler(ImagingHandler):
    @classmethod
    def regex(cls):
        return (
            r'/'
            r'(?P<project>[^-/]+)/'
            r'(?P<language>[^/]+)/'
            r'thumb/'
            r'(?P<shard1>[0-9a-zA-Z]+)/'
            r'(?P<shard2>[0-9a-zA-Z]+)/'
            r'(?P<filename>.*)/'
            r'(?:(?P<qlow>qlow-))?'
            r'(?:(?P<lossy>lossy-))?'
            r'(?:page(?P<page>\d+)-)?'
            r'(?:lang(?P<lang>[a-zA-Z]+)-)?'
            r'(?P<width>\d+)px-'
            r'(?:(?P<seek>\d+)-)?'
            r'(?P<end>.*)'
            r'\.(?P<format>[a-zA-Z]+)'
        )

    def reconstruct_path(self, kw):
        path = '/'.join((kw['shard1'], kw['shard2'], kw['filename'], ''))

        if kw['qlow'] == 'qlow-':
            path += kw['qlow']

        if kw['lossy'] == 'lossy-':
            path += kw['lossy']

        if kw['page']:
            path += 'page' + kw['page'] + '-'

        if kw['lang']:
            path += 'lang' + kw['lang'] + '-'

        path += kw['width'] + 'px-'

        if kw['seek']:
            path += kw['seek'] + '-'

        path += kw['end']

        path += '.' + kw['format']

        return path

    @tornado.web.asynchronous
    def get(self, **kw):
        translated_kw = self.translate(kw)
        return super(ImagesHandler, self).get(**translated_kw)

    @tornado.web.asynchronous
    def head(self, **kw):
        translated_kw = self.translate(kw)
        return super(ImagesHandler, self).head(**translated_kw)

    def translate(self, kw):
        filepath = '/'.join((kw['shard1'], kw['shard2'], kw['filename']))

        translated = {'unsafe': 'unsafe'}
        translated['width'] = kw['width']

        sharded_containers = []

        if hasattr(self.context.config, 'SWIFT_SHARDED_CONTAINERS'):
            sharded_containers = self.context.config.SWIFT_SHARDED_CONTAINERS

        project = kw['project']
        language = kw['language']

        # Legacy special cases taken from rewrite.py
        if project == 'wikipedia':
            if language in ('meta', 'commons', 'internal', 'grants'):
                project = 'wikimedia'
            if language == 'mediawiki':
                project = 'mediawiki'
                language = 'www'

        projlang = '-'.join((project, language))
        original_container = projlang + '-local-public'
        thumbnail_container = projlang + '-local-thumb'

        shard = '.' + kw['shard2']

        if original_container in sharded_containers:
            original_container += shard

        if thumbnail_container in sharded_containers:
            thumbnail_container += shard

        swift_uri = (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_API_PATH +
            original_container
        )

        swift_uri += '/'

        translated['image'] = swift_uri + filepath

        filters = []

        if kw['format'] in ('jpe', 'jpeg'):
            kw['format'] = 'jpg'

        if kw['format'] == 'jpg':
            if (
                kw['qlow'] == 'qlow-' and
                hasattr(self.context.config, 'QUALITY_LOW')
            ):
                filters.append('quality(%d)' % self.context.config.QUALITY_LOW)

            if hasattr(self.context.config, 'DEFAULT_FILTERS_JPEG'):
                filters.append(self.context.config.DEFAULT_FILTERS_JPEG)

        filters.append('format(%s)' % kw['format'])

        page = kw.get('page', kw['seek'])

        if page:
            filters.append('page(%s)' % page)

        lang = kw.get('lang')

        if lang:
            filters.append('lang(%s)' % lang)

        if filters:
            translated['filters'] = ':'.join(filters)

        self.context.request_handler.set_header(
            'xkey',
            u'File:' + kw['filename']
        )

        self.context.request_handler.set_header(
            'Content-Disposition',
            u'inline;filename*=UTF-8\'\'' + kw['filename']
        )

        # Save wikimedia-specific save path information
        # Which will later be used by result storage
        self.context.wikimedia_thumbnail_container = thumbnail_container
        self.context.wikimedia_path = self.reconstruct_path(kw)

        if hasattr(self.context.config, 'SWIFT_PATH_PREFIX'):
            self.context.wikimedia_path = (
                self.context.config.SWIFT_PATH_PREFIX +
                self.context.wikimedia_path
            )

        return translated
