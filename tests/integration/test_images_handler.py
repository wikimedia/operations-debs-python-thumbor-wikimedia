import json
from thumbor.config import Config
from thumbor.handlers import BaseHandler


from . import WikimediaTestCase


class WikimediaImagesHandlerTestCase(WikimediaTestCase):
    def setUp(self):
        super(WikimediaImagesHandlerTestCase, self).setUp()

        # Undo monkey-patching to be able to inspect headers
        # as if the test requests were successful
        def _error(self, status, msg=None):
            return BaseHandler._old_error(self, status, msg)

        BaseHandler._error = _error

    def tearDown(self):
        BaseHandler._error = BaseHandler._error
        super(WikimediaImagesHandlerTestCase, self).tearDown()

    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.images',
            'wikimedia_thumbor.handler.core'
        ]

        cfg.SWIFT_HOST = 'http://swifthost'
        cfg.SWIFT_API_PATH = '/swift/v1/api/path'
        cfg.SWIFT_AUTH_PATH = '/auth/v1.0'
        cfg.SWIFT_USER = 'foo:bar'
        cfg.SWIFT_KEY = 'baz'
        cfg.SWIFT_SHARDED_CONTAINERS = [
            'wikipedia-en-local-public',
            'wikipedia-en-local-temp',
            'wikipedia-en-local-thumb',
            'wikipedia-commons-local-public',
            'wikipedia-commons-local-thumb'
        ]
        cfg.SWIFT_PATH_PREFIX = 'thumbor/'
        cfg.SWIFT_CONNECTION_TIMEOUT = 1
        cfg.SWIFT_RETRIES = 0
        cfg.SWIFT_PRIVATE_SECRET = 'topsecret1234'

        cfg.QUALITY_LOW = 10
        cfg.DEFAULT_FILTERS_JPEG = 'conditional_sharpen(0.0,0.8,1.0,0.0,0.85)'

        return cfg

    def run_and_check_headers(
        self,
        url,
        headers,
        expected_xkey,
        expected_original_container,
        expected_original_path,
        expected_thumbnail_container,
        expected_thumbnail_path,
        expected_width,
        expected_image,
        expected_filters,
        expected_content_disposition
    ):
        """Request URL and check header correctness.

        Arguments:
        url -- thumbnail URL
        expected_xkey -- expected xkey
        expected_original_container -- expected original swift container
        expected_original_path -- expected original swift path
        expected_thumbnail_container -- expected thumbnail swift container
        expected_thumbnaill_path -- expected thumbnail swift path
        expected_width -- expected width
        expected_image -- expected image
        expected_filters -- expected thumbor filters
        expected_content_disposition -- expected content disposition
        """
        response = self.retrieve(url, headers)

        try:
            xkey = response.headers.get_list('xkey')[0]
        except IndexError:
            xkey = None

        try:
            wikimedia_original_container = response.headers.get_list(
                'Thumbor-Wikimedia-Original-Container'
            )[0]
        except IndexError:
            wikimedia_original_container = None

        try:
            wikimedia_original_path = response.headers.get_list(
                'Thumbor-Wikimedia-Original-Path'
            )[0]
        except IndexError:
            wikimedia_original_path = None

        try:
            wikimedia_thumbnail_container = response.headers.get_list(
                'Thumbor-Wikimedia-Thumbnail-Container'
            )[0]
        except IndexError:
            wikimedia_thumbnail_container = None

        try:
            wikimedia_thumbnail_path = response.headers.get_list(
                'Thumbor-Wikimedia-Thumbnail-Path'
            )[0]
        except IndexError:
            wikimedia_thumbnail_path = None

        try:
            thumbor_parameters = json.loads(
                response.headers.get_list('Thumbor-Parameters')[0]
            )
        except IndexError:
            thumbor_parameters = {
                'width': None,
                'image': None,
                'filters': None
            }

        try:
            wikimedia_content_diposition = response.headers.get_list(
                'Content-Disposition'
            )[0]
        except IndexError:
            wikimedia_content_diposition = None

        assert xkey == expected_xkey, 'Incorrect Xkey: %s' % xkey

        assert wikimedia_original_container == expected_original_container, \
            'Thumbor-Wikimedia-Original-Container: %s' % wikimedia_original_container

        assert wikimedia_original_path == expected_original_path, \
            'Thumbor-Wikimedia-Original-Path: %s' % wikimedia_original_path

        assert wikimedia_thumbnail_container == expected_thumbnail_container, \
            'Thumbor-Wikimedia-Thumbnail-Container: %s' % wikimedia_thumbnail_container

        assert wikimedia_thumbnail_path == expected_thumbnail_path, \
            'Thumbor-Wikimedia-Thumbnail-Path: %s' % wikimedia_thumbnail_path

        assert thumbor_parameters['width'] == expected_width, \
            'Thumbor-Parameters width: %s' % thumbor_parameters['width']

        assert thumbor_parameters['image'] == expected_image, \
            'Thumbor-Parameters image: %s' % thumbor_parameters['image']

        assert thumbor_parameters['filters'] == expected_filters, \
            'Thumbor-Parameters filters: %s' % thumbor_parameters['filters']

        assert wikimedia_content_diposition == expected_content_disposition, \
            'Content-Disposition: %s' % wikimedia_content_diposition

    def test_png(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png',
            None,
            'File:1Mcolors.png',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.png',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.png',
            'format(png)',
            'inline;filename*=UTF-8\'\'1Mcolors.png'
        )

    def test_qlow(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.jpg/qlow-400px-1Mcolors.jpg',
            None,
            'File:1Mcolors.jpg',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.jpg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.jpg/qlow-400px-1Mcolors.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.jpg',
            'quality(10):conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(jpg)',
            'inline;filename*=UTF-8\'\'1Mcolors.jpg'
        )

    def test_page(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.pdf/page3-400px-1Mcolors.pdf.jpg',
            None,
            'File:1Mcolors.pdf',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.pdf',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.pdf/page3-400px-1Mcolors.pdf.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.pdf',
            'format(jpg):page(3)',
            'inline;filename*=UTF-8\'\'1Mcolors.pdf.jpg'
        )

    def test_lang(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.svg/langfr-400px-1Mcolors.svg.png',
            None,
            'File:1Mcolors.svg',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.svg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.svg/langfr-400px-1Mcolors.svg.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.svg',
            'format(png):lang(fr)',
            'inline;filename*=UTF-8\'\'1Mcolors.svg.png'
        )
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.svg/langzh-hans-400px-1Mcolors.svg.png',
            None,
            'File:1Mcolors.svg',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.svg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.svg/langzh-hans-400px-1Mcolors.svg.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.svg',
            'format(png):lang(zh-hans)',
            'inline;filename*=UTF-8\'\'1Mcolors.svg.png'
        )

    def test_seek(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.webm/400px-seek=10-1Mcolors.webm.jpg',
            None,
            'File:1Mcolors.webm',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.webm',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.webm/400px-seek=10-1Mcolors.webm.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.webm',
            'format(jpg):page(10)',
            'inline;filename*=UTF-8\'\'1Mcolors.webm.jpg'
        )

    def test_jpe(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.jpe/400px-1Mcolors.jpe',
            None,
            'File:1Mcolors.jpe',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.jpe',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.jpe/400px-1Mcolors.jpe',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.jpe',
            'conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(jpg)',
            'inline;filename*=UTF-8\'\'1Mcolors.jpe'
        )

    def test_jpeg(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.jpeg/400px-1Mcolors.jpeg',
            None,
            'File:1Mcolors.jpeg',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.jpeg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.jpeg/400px-1Mcolors.jpeg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.jpeg',
            'conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(jpg)',
            'inline;filename*=UTF-8\'\'1Mcolors.jpeg'
        )

    def test_webp(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.jpg/400px-1Mcolors.jpg.webp',
            None,
            'File:1Mcolors.jpg',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.jpg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.jpg/400px-1Mcolors.jpg.webp',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.jpg',
            'conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(webp)',
            'inline;filename*=UTF-8\'\'1Mcolors.jpg.webp'
        )
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png.webp',
            None,
            'File:1Mcolors.png',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.png',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png.webp',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.png',
            'format(webp)',
            'inline;filename*=UTF-8\'\'1Mcolors.png.webp'
        )
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.pdf/400px-1Mcolors.pdf.jpg.webp',
            None,
            'File:1Mcolors.pdf',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.pdf',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.pdf/400px-1Mcolors.pdf.jpg.webp',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.pdf',
            'format(webp)',
            'inline;filename*=UTF-8\'\'1Mcolors.pdf.webp'
        )

    def test_meta(self):
        self.run_and_check_headers(
            '/wikipedia/meta/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png',
            None,
            'File:1Mcolors.png',
            'wikipedia-meta-local-public',
            'd/d3/1Mcolors.png',
            'wikipedia-meta-local-thumb',
            'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-meta-local-public/d/d3/1Mcolors.png',
            'format(png)',
            'inline;filename*=UTF-8\'\'1Mcolors.png'
        )

    def test_mediawiki(self):
        self.run_and_check_headers(
            '/wikipedia/mediawiki/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png',
            None,
            'File:1Mcolors.png',
            'wikipedia-mediawiki-local-public',
            'd/d3/1Mcolors.png',
            'wikipedia-mediawiki-local-thumb',
            'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-mediawiki-local-public/d/d3/1Mcolors.png',
            'format(png)',
            'inline;filename*=UTF-8\'\'1Mcolors.png'
        )

    def test_archive(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/archive/d/d3/20160729183014!1Mcolors.jpg/400px-1Mcolors.jpg',
            None,
            'File:20160729183014!1Mcolors.jpg',
            'wikipedia-en-local-public.d3',
            'archive/d/d3/20160729183014!1Mcolors.jpg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/archive/d/d3/20160729183014!1Mcolors.jpg/400px-1Mcolors.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/archive/d/d3/20160729183014!1Mcolors.jpg',
            'conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(jpg)',
            'inline;filename*=UTF-8\'\'20160729183014%211Mcolors.jpg'
        )

    def test_lossless_tiff(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.tif/lossless-page1-400px-1Mcolors.tif.png',
            None,
            'File:1Mcolors.tif',
            'wikipedia-en-local-public.d3',
            'd/d3/1Mcolors.tif',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.tif/lossless-page1-400px-1Mcolors.tif.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1Mcolors.tif',
            'format(png):page(1)',
            'inline;filename*=UTF-8\'\'1Mcolors.tif.png'
        )

    def test_broken_request(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1M%0Acolors.tif/lossless-page1-400px-1Mcolors.tif.png',
            None,
            None,
            'wikipedia-en-local-public.d3',
            None,
            'wikipedia-en-local-thumb.d3',
            None,
            '400',
            'http://swifthost/swift/v1/api/path/'
            + 'wikipedia-en-local-public.d3/d/d3/1M\ncolors.tif',
            'format(png):page(1)',
            'inline;filename*=UTF-8\'\'1M%0Acolors.tif.png'
        )

    def test_question_mark_original(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1M%3Fcolors.tif/lossless-page1-400px-1Mcolors.tif.png',
            None,
            'File:1M?colors.tif',
            'wikipedia-en-local-public.d3',
            'd/d3/1M?colors.tif',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1M?colors.tif/lossless-page1-400px-1Mcolors.tif.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/d/d3/1M?colors.tif',
            'format(png):page(1)',
            'inline;filename*=UTF-8\'\'1M%3Fcolors.tif.png'
        )

    def test_percentage_original(self):
        self.run_and_check_headers(
            '/wikipedia/commons/thumb/c/ce/Dramatische_daling_insectenpopulatie%2C_75%25_is_verdwenen.webm/800px--Dramatische_daling_insectenpopulatie%2C_75%25_is_verdwenen.webm.jpg',
            None,
            'File:Dramatische_daling_insectenpopulatie,_75%_is_verdwenen.webm',
            'wikipedia-commons-local-public.ce',
            'c/ce/Dramatische_daling_insectenpopulatie,_75%_is_verdwenen.webm',
            'wikipedia-commons-local-thumb.ce',
            'thumbor/c/ce/Dramatische_daling_insectenpopulatie,_75%_is_verdwenen.webm/800px--Dramatische_daling_insectenpopulatie,_75%_is_verdwenen.webm.jpg',
            '800',
            'http://swifthost/swift/v1/api/path/wikipedia-commons-local-public.ce/c/ce/Dramatische_daling_insectenpopulatie,_75%_is_verdwenen.webm',
            'format(jpg)',
            'inline;filename*=UTF-8\'\'Dramatische_daling_insectenpopulatie%2C_75%25_is_verdwenen.webm.jpg'
        )

    def test_temp(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/temp/8/88/20161115090130%21fYJSjm.pdf/page1-71px-20161115090130%21fYJSjm.pdf.jpg',
            {'X-Swift-Secret' : 'topsecret1234'},
            'File:20161115090130!fYJSjm.pdf',
            'wikipedia-en-local-temp.57',
            '5/57/20161115090130!fYJSjm.pdf',
            'wikipedia-en-local-temp.88',
            'thumbor/thumb/8/88/20161115090130!fYJSjm.pdf/page1-71px-20161115090130!fYJSjm.pdf.jpg',
            '71',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-temp.57/5/57/20161115090130!fYJSjm.pdf',
            'format(jpg):page(1)',
            'inline;filename*=UTF-8\'\'20161115090130%21fYJSjm.pdf.jpg'
        )

    def run_and_check_error(
        self,
        url,
        expected_status
    ):
        response = self.retrieve(url)
        assert response.code == expected_status

    def test_missing_mandatory_parameters(self):
        self.run_and_check_error(
            '/wikipedia/en/thumb/d/d3/1Mcolors.tif',
            404
        )

    def test_too_many_parts(self):
        self.run_and_check_error(
            '/wikipedia/en/thumb/8/80/1Mcolors.tif/1Mcolors.tif.jpg/90x55x2-15px-1Mcolors.tif.jpg',
            404
        )
        self.run_and_check_error(
            '/wikipedia/en/thumb/7/77/1Mcolors.png/1Mcolors.png/199px-1Mcolors.png',
            404
        )
