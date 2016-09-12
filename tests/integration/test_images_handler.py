import json
from thumbor.config import Config


from . import WikimediaTestCase


class WikimediaImagesHandlerTestCase(WikimediaTestCase):
    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.images'
        ]

        cfg.SWIFT_HOST = 'http://swifthost'
        cfg.SWIFT_API_PATH = '/swift/v1/api/path/'
        cfg.SWIFT_AUTH_PATH = '/auth/v1.0'
        cfg.SWIFT_USER = 'foo:bar'
        cfg.SWIFT_KEY = 'baz'
        cfg.SWIFT_SHARDED_CONTAINERS = [
            'wikipedia-en-local-public',
            'wikipedia-en-local-thumb'
        ]
        cfg.SWIFT_PATH_PREFIX = 'thumbor/'
        cfg.SWIFT_CONNECTION_TIMEOUT = 1
        cfg.SWIFT_RETRIES = 0

        cfg.QUALITY_LOW = 10
        cfg.DEFAULT_FILTERS_JPEG = 'conditional_sharpen(0.0,0.8,1.0,0.0,0.85)'

        return cfg

    def run_and_check_headers(
        self,
        url,
        expected_xkey,
        expected_container,
        expected_path,
        expected_width,
        expected_image,
        expected_filters
    ):
        """Request URL and check header correctness.

        Arguments:
        url -- thumbnail URL
        expected_xkey -- expected xkey header value
        expected_container -- expected container header value
        expected_path -- expected path header value
        expected_width -- expected width header value
        expected_image -- expected image header value
        expected_filters -- expected filters header value
        """
        response = self.retrieve(url)

        xkey = response.headers.get_list('xkey')[0]
        wikimedia_path = response.headers.get_list('Wikimedia-Path')[0]
        wikimedia_thumbnail_container = response.headers.get_list(
            'Wikimedia-Thumbnail-Container'
        )[0]
        thumbor_parameters = json.loads(
            response.headers.get_list('Thumbor-Parameters')[0]
        )

        assert xkey == expected_xkey, 'Incorrect Xkey: %s' % xkey
        assert wikimedia_path == expected_path, \
            'Wikimedia-Path: %s' % wikimedia_path
        assert wikimedia_thumbnail_container == expected_container, \
            'Wikimedia-Thumbnail-Container: %s' % wikimedia_thumbnail_container
        assert thumbor_parameters['width'] == expected_width, \
            'Thumbor-Parameters width: %s' % thumbor_parameters['width']
        assert thumbor_parameters['image'] == expected_image, \
            'Thumbor-Parameters image: %s' % thumbor_parameters['image']
        assert thumbor_parameters['filters'] == expected_filters, \
            'Thumbor-Parameters filters: %s' % thumbor_parameters['filters']

    def test_png(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png',
            'File:1Mcolors.png',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/'
            + 'd/d3/1Mcolors.png',
            'format(png)'
        )

    def test_qlow(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.jpg/qlow-400px-1Mcolors.jpg',
            'File:1Mcolors.jpg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.jpg/qlow-400px-1Mcolors.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/'
            + 'd/d3/1Mcolors.jpg',
            'quality(10):conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(jpg)'
        )

    def test_page(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.pdf/'
            + 'page3-400px-1Mcolors.pdf.jpg',
            'File:1Mcolors.pdf',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.pdf/page3-400px-1Mcolors.pdf.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/'
            + 'd/d3/1Mcolors.pdf',
            'format(jpg):page(3)'
        )

    def test_lang(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.svg/'
            + 'langfr-400px-1Mcolors.svg.png',
            'File:1Mcolors.svg',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.svg/langfr-400px-1Mcolors.svg.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/'
            + 'd/d3/1Mcolors.svg',
            'format(png):lang(fr)'
        )

    def test_seek(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.webm/'
            + '400px-seek=10-1Mcolors.webm.jpg',
            'File:1Mcolors.webm',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.webm/400px-seek=10-1Mcolors.webm.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/'
            + 'd/d3/1Mcolors.webm',
            'format(jpg):page(10)'
        )

    def test_jpe(self):
        self.run_and_check_headers(
            '/wikipedia/en/thumb/d/d3/1Mcolors.jpe/400px-1Mcolors.jpe',
            'File:1Mcolors.jpe',
            'wikipedia-en-local-thumb.d3',
            'thumbor/d/d3/1Mcolors.jpe/400px-1Mcolors.jpg',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-en-local-public.d3/'
            + 'd/d3/1Mcolors.jpe',
            'conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(jpg)'
        )

    def test_meta(self):
        self.run_and_check_headers(
            '/wikipedia/meta/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png',
            'File:1Mcolors.png',
            'wikipedia-meta-local-thumb',
            'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-meta-local-public/'
            + 'd/d3/1Mcolors.png',
            'format(png)'
        )

    def test_mediawiki(self):
        self.run_and_check_headers(
            '/wikipedia/mediawiki/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png',
            'File:1Mcolors.png',
            'wikipedia-mediawiki-local-thumb',
            'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png',
            '400',
            'http://swifthost/swift/v1/api/path/wikipedia-mediawiki-local-public/'
            + 'd/d3/1Mcolors.png',
            'format(png)'
        )
