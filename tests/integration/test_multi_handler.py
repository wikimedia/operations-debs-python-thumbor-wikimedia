from tornado.httputil import HTTPHeaders
from thumbor.config import Config
from wikimedia_thumbor.handler.multi import MultiHandler


from . import WikimediaTestCase


class WikimediaMultiHandlerTestCase(WikimediaTestCase):
    def setUp(self):
        super(WikimediaMultiHandlerTestCase, self).setUp()
        self.old_limit = MultiHandler.paths_limit
        MultiHandler.paths_limit = 2

    def tearDown(self):
        super(WikimediaMultiHandlerTestCase, self).tearDown()
        MultiHandler.paths_limit = self.old_limit

    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.multi'
        ]

        return cfg

    def test_multi(self):
        headers = HTTPHeaders(
            {'Content-Type': 'application/x-www-form-urlencoded'}
        )

        self.http_client.fetch(
            self.get_url('/multi'),
            self.stop,
            method='POST',
            headers=headers,
            body='paths[]=unsafe%2F400x%2F1Mcolors.png&'
            + 'paths[]=unsafe%2F300x%2F1Mcolors.png'
        )
        response = self.wait()
        assert response.code == 200, \
            'Unexpected response code: %r %r' % (response.code, response.body)

    def test_multi_max_paths(self):
        headers = HTTPHeaders(
            {'Content-Type': 'application/x-www-form-urlencoded'}
        )

        self.http_client.fetch(
            self.get_url('/multi'),
            self.stop,
            method='POST',
            headers=headers,
            body='paths[]=unsafe%2F400x%2F1Mcolors.png&'
            + 'paths[]=unsafe%2F300x%2F1Mcolors.png&'
            + 'paths[]=unsafe%2F200x%2F1Mcolors.png'
        )
        response = self.wait()
        assert response.code == 400, \
            'Unexpected response code: %r %r' % (response.code, response.body)
