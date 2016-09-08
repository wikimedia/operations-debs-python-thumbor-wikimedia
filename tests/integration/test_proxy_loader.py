from . import WikimediaTestCase


class WikimediaProxyLoaderTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaProxyLoaderTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.proxy'
        cfg.PROXY_LOADER_LOADERS = [
            'wikimedia_thumbor.loader.video'
        ]
        return cfg

    def test_proxied_video(self):
        self.run_and_check_ssim_and_size(
            'unsafe/320x/filters:page(1)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/a/a3/Aequipotentialflaechen.webm',
            '320px-seek=1-Aequipotentialflaechen.webm.jpg',
            0.99,
            1.0,
        )

    def test_proxied_png(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/'
            + 'd/d6/1Mcolors.png',
            '400px-1Mcolors.png',
            0.99,
            1.0,
        )