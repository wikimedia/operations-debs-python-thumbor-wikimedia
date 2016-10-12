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

    def test_proxied_uppercase_ogg(self):
        self.run_and_check_ssim_and_size(
            'unsafe/300x/https://upload.wikimedia.org/wikipedia/commons/f/f2/'
            + 'Shakinghands_high.OGG',
            '300px--Shakinghands_high.OGG.jpg',
            0.96,
            1.1
        )

    def test_proxied_gif(self):
        self.run_and_check_ssim_and_size(
            'unsafe/300x/https://upload.wikimedia.org/wikipedia/commons/f/fb/'
            + 'Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            0.98,
            1.1
        )
