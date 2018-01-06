# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler translates mediawiki thumbnail urls into thumbor urls
# And sets the xkey for Varnish purging purposes

from functools import partial
from urllib import quote
import json
import hashlib
import md5
import memcache
import random
import tornado.ioloop
import tornado.gen as gen

from thumbor.context import RequestParameters
from thumbor.handlers import BaseHandler
from thumbor.handlers.imaging import ImagingHandler
from thumbor.utils import logger

from wikimedia_thumbor.poolcounter import PoolCounter


BaseHandler._old_error = BaseHandler._error


# We need to monkey-patch BaseHandler because otherwise we
# wouldn't apply the Cache-Control headers to 400 errors that
# don't make it to ImagesHandler since they don't match the
# handlers' regexp.
def _error(self, status, msg=None):
    # If the error isn't due to throttling, we increase a
    # failure counter for the given xkey, which will let us
    # avoid re-trying thumbnails bound to fail too many times
    xkey = self._headers.get('xkey', False)
    mc = self.failure_memcache()
    if status != 429 and status != 404 and xkey and mc:
        key = self._mc_encode_key(xkey)
        counter = mc.get(key)
        if not counter:
            # We add randomness to the expiry to avoid stampedes
            duration = self.context.config.get('FAILURE_THROTTLING_DURATION', 3600)
            mc.set(key, '1', duration + random.randint(0, 300))
        else:
            mc.incr(key)

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

    if status == 429:
        # 429 is missing from httplib.responses
        self.set_status(status, 'Too Many Requests')
    else:
        self.set_status(status)

    if msg is not None:
        try:
            logger.warn(msg, extra={'url': self.context.request.url})
        except AttributeError:
            logger.warn(msg)
    self.finish()


def _mc(self):
    if not hasattr(self.context.config, 'FAILURE_THROTTLING_MEMCACHE'):
        return False

    if hasattr(self, 'failure_mc'):
        return self.failure_mc

    self.failure_mc = memcache.Client(self.context.config.FAILURE_THROTTLING_MEMCACHE)
    return self.failure_mc


def _mc_encode_key(self, key):
    # Encoding is safe to do only in the unicode case,
    # else we can't assume a specific encoding
    if type(key) is unicode:
        keybytes = bytes(key.encode('utf8', 'ignore'))
    else:
        keybytes = bytes(key)
    keyhash = hashlib.sha256(keybytes).hexdigest()
    prefix = self.context.config.get('FAILURE_THROTTLING_PREFIX', '')
    return prefix + 'sha256:' + keyhash


BaseHandler._mc_encode_key = _mc_encode_key

BaseHandler.failure_memcache = _mc

BaseHandler._error = _error


def close_poolcounter(pc):
    logger.debug('[ImagesHandler] PoolCounter cleanup callback')
    if pc:
        pc.close()


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
            r'(?:lang(?P<lang>[0-9a-zA-Z-]+)-)?'
            r'(?P<width>\d+)px-'
            r'(?:(?:seek=|seek%3D)(?P<seek>\d+)-)?'
            r'(?P<end>[^/]+)'
            r'\.(?P<format>[0-9a-zA-Z]+)'
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

        private_containers = []

        if hasattr(self.context.config, 'SWIFT_PRIVATE_CONTAINERS'):
            private_containers = self.context.config.SWIFT_PRIVATE_CONTAINERS

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

        self.context.private = original_container in private_containers

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
            self.context.config.SWIFT_API_PATH + '/' +
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
        xkey = u'File:' + original_filename

        self.safe_set_header('xkey', xkey)

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

        self.safe_set_header(
            'Request-Date',
            self.request.headers.get('Request-Date', 'None')
        )

        return xkey

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

        if self.context.private:
            received_secret = self.request.headers.get('X-Swift-Secret', False)
            secret = self.context.config.get('SWIFT_PRIVATE_SECRET', False)
            if not secret or not received_secret or received_secret != secret:
                self._error(
                    401,
                    'Unauthorized access to private Swift container'
                )
                return

        xkey = self.set_headers(translated_kw)
        mc = self.failure_memcache()

        if mc and xkey:
            key = self._mc_encode_key(xkey)
            counter = mc.get(key)
            if counter and int(counter) >= self.context.config.get('FAILURE_THROTTLING_MAX', 4):
                self._error(
                    429,
                    'Too many thumbnail requests for failing image'
                )
                return

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

        throttled = yield self.poolcounter_throttle(translated_kw['image'], kw['extension'])

        if throttled:
            return

        self.execute_image_operations()

    def finish(self):
        if hasattr(self, 'pc') and self.pc:
            self.pc.close()
            self.pc = None

        mc = self.failure_memcache()
        if mc:
            mc.disconnect_all()

        super(ImagesHandler, self).finish()

        self.context.metrics.incr('response.status.' + str(self.get_status()))

    @gen.coroutine
    def poolcounter_throttle_key(self, key, cfg):
        try:
            lock_acquired = yield self.pc.acq4me(key, cfg['workers'], cfg['maxqueue'], cfg['timeout'])
        except tornado.iostream.StreamClosedError:
            # If something is wrong with poolcounter, don't throttle
            logger.error('[ImagesHandler] Failed to leverage PoolCounter')
            self.context.metrics.incr('poolcounter.failure')
            raise tornado.gen.Return(False)

        if lock_acquired:
            self.context.metrics.incr('poolcounter.locked')
            raise tornado.gen.Return(False)

        self.context.metrics.incr('poolcounter.throttled')

        self.pc.close()
        self.pc = None

        log_extra = {'url': self.context.request.url}
        logger.error('[ImagesHandler] Throttled by PoolCounter: %s %r' % (key, cfg), extra=log_extra)

        self._error(
            429,
            'Too many thumbnail requests'
        )
        raise tornado.gen.Return(True)

    @gen.coroutine
    def poolcounter_throttle(self, filename, extension):
        self.pc = None

        if not self.context.config.get('POOLCOUNTER_SERVER', False):
            raise tornado.gen.Return(False)

        self.pc = PoolCounter(self.context)

        cfg = self.context.config.get('POOLCOUNTER_CONFIG_PER_IP', False)
        if cfg:
            ff = self.request.headers.get('X-Forwarded-For', False)
            if not ff:
                logger.warn('[ImagesHandler] No X-Forwarded-For header in request, cannot throttle per IP')
            else:
                ff = ff.split(', ')[0]
                throttled = yield self.poolcounter_throttle_key('thumbor-ip-%s' % ff, cfg)

                if throttled:
                    raise tornado.gen.Return(True)

        cfg = self.context.config.get('POOLCOUNTER_CONFIG_PER_ORIGINAL', False)
        if cfg:
            name_sha1 = hashlib.sha1(filename).hexdigest()

            throttled = yield self.poolcounter_throttle_key('thumbor-render-%s' % name_sha1, cfg)

            if throttled:
                raise tornado.gen.Return(True)

        cfg = self.context.config.get('POOLCOUNTER_CONFIG_EXPENSIVE', False)
        if cfg and extension.lower() in cfg['extensions']:
            throttled = yield self.poolcounter_throttle_key('thumbor-render-expensive', cfg)

            if throttled:
                raise tornado.gen.Return(True)

        # This closes the PoolCounter connection in case it hasn't been closed normally.
        # Which can happen if an exception occured while processing the file, for example.
        release_timeout = self.context.config.get('POOLCOUNTER_RELEASE_TIMEOUT', False)
        if release_timeout:
            logger.debug('[ImagesHandler] Setting up PoolCounter cleanup callback')
            tornado.ioloop.IOLoop.instance().call_later(
                release_timeout,
                partial(close_poolcounter, self.pc)
            )

        raise tornado.gen.Return(False)

    # With our IM engine, exceptions may occur during _load_results
    # Which Thumbor doesn't handle gracefully
    # This should be fixed in Thumbor 6.3.0:
    # https://github.com/thumbor/thumbor/commit/9fba8e62ae339eb9a0ab5bbdfb2ef1318b20db13
    # When we upgrade to Thumbor >= 6.3.0 we should be able to remove these overrides
    # on _load_results, _write_results_to_client and _store_results
    def _load_results(self, context):
        try:
            results, content_type = BaseHandler._load_results(self, context)
        except Exception:
            logger.exception('[ImagesHandler] Exception during _load_results')
            self._error(500)
            return None, None

        return results, content_type

    # Similarly, after the _load_requests neutering happening above, thumbor
    # Would still try to send a response to the client after the 500 error
    def _write_results_to_client(self, context, results, content_type):
        if results is not None:
            BaseHandler._write_results_to_client(self, context, results, content_type)

    # ... and would also try to store empty results
    def _store_results(self, context, results):
        if results is not None:
            BaseHandler._store_results(self, context, results)
