from functools import partial
import os
from urllib3.response import HTTPResponse as UrlLib3HTTPResponse
from requests.adapters import HTTPAdapter
from swiftclient.client import Connection
from thumbor.config import Config
from tornado.simple_httpclient import SimpleAsyncHTTPClient


from . import WikimediaTestCase


class WikimediaSwiftTestCase(WikimediaTestCase):
    def setUp(self):
        super(WikimediaSwiftTestCase, self).setUp()

        self.original_send = HTTPAdapter.send

        def send(
            self,
            request,
            stream=False,
            timeout=None,
            verify=True,
            cert=None,
            proxies=None
        ):
            resp = UrlLib3HTTPResponse(status=200)
            return self.build_response(request, resp)

        HTTPAdapter.send = send
        self.original_fetch_impl = SimpleAsyncHTTPClient.fetch_impl
        original_fetch_impl = self.original_fetch_impl

        def override_callback(request, original_callback, response):
            expected = 'http://swifthost/swift/v1/api/path/' \
                + 'wikipedia-en-local-public/d/d3/1Mcolors.png'
            if request.request.url == expected:
                response.error = False
                response.code = 200
                response.buffer = True
                path = os.path.join(
                    os.path.dirname(__file__),
                    'originals',
                    '1Mcolors.png'
                )
                with open(path, 'r') as f:
                    response._body = f.read()

            original_callback(response)

        def fetch_impl(self, request, callback):
            original_fetch_impl(
                self,
                request,
                partial(override_callback, request, callback)
            )

        SimpleAsyncHTTPClient.fetch_impl = fetch_impl
        self.original_put_object = Connection.put_object

        def put_object(self, container, obj, contents, content_length=None,
                       etag=None, chunk_size=None, content_type=None,
                       headers=None, query_string=None, response_dict=None):
            assert container == 'wikipedia-en-local-thumb.d3', \
                'Unexpected swift container: %r' % container
            assert obj == 'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png', \
                'Unexpected swift obj: %r' % obj
            assert headers == {'xkey': 'File:1Mcolors.png'}, \
                'Unexpected swift headers: %r' % headers

        Connection.put_object = put_object

    def tearDown(self):
        super(WikimediaSwiftTestCase, self).tearDown()
        HTTPAdapter.send = self.original_send
        SimpleAsyncHTTPClient.fetch_impl = self.original_fetch_impl
        Connection.put_object = self.original_put_object

        if hasattr(self, 'original_get_object'):
            Connection.get_object = self.original_get_object

    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.images'
        ]

        cfg.STORAGE = 'wikimedia_thumbor.storage.request'
        cfg.RESULT_STORAGE = 'wikimedia_thumbor.result_storage.swift'
        cfg.RESULT_STORAGE_STORES_UNSAFE = True
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

        cfg.QUALITY_LOW = 10
        cfg.DEFAULT_FILTERS_JPEG = 'conditional_sharpen(0.6,0.01,false,0.85)'

        return cfg

    def test_swift(self):
        self.retrieve(
            '/wikipedia/en/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png'
        )

        self.original_get_object = Connection.get_object

        def get_object(self, container, obj, resp_chunk_size=None,
                       query_string=None, response_dict=None, headers=None):
            assert container == 'wikipedia-en-local-thumb.d3', \
                'Unexpected swift container: %r' % container
            assert obj == 'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png', \
                'Unexpected swift obj: %r' % obj

            path = os.path.join(
                os.path.dirname(__file__),
                'thumbnails',
                '400px-1Mcolors.png'
            )
            with open(path, 'r') as f:
                return {'xkey': 'File:1Mcolors.png'}, f.read()

        Connection.get_object = get_object

        self.retrieve(
            '/wikipedia/en/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png'
        )
