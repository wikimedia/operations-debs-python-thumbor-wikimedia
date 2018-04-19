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
            'thumbor/unsafe/320x/filters:page(1)/https://upload.wikimedia.org/wikipedia/commons/a/a3/Aequipotentialflaechen.webm',
            '320px-seek=1-Aequipotentialflaechen.webm.jpg',
            '320px-seek=1-Aequipotentialflaechen.webm.png',
            320,
            240,
            0.99,
            0.81
        )

    def test_proxied_png(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/d/d6/1Mcolors.png',
            '400px-1Mcolors.png',
            '400px-1Mcolors.png',
            400,
            400,
            0.99,
            0.74
        )

    def test_proxied_gif(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/https://upload.wikimedia.org/wikipedia/commons/f/fb/Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            300,
            187,
            0.98,
            1.11
        )
