from thumbor.config import Config


from . import WikimediaTestCase


class WikimediaHealthcheckHandlerTestCase(WikimediaTestCase):
    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.healthcheck'
        ]

        return cfg

    def test_healthcheck(self):
        self.http_client.fetch(
            self.get_url('/healthcheck'),
            self.stop,
            method='GET'
        )
        response = self.wait()

        assert response.code == 200, 'Unexpected response code: %r' % response.code
        assert response.body == 'WORKING', 'Unexpected response body: %r' % response.body
