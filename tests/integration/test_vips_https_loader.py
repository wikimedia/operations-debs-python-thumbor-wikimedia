from . import WikimediaTestCase


class WikimediaVipsHttpsLoaderTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaVipsHttpsLoaderTest, self).get_config()
        cfg.VIPS_ENGINE_MIN_PIXELS = 0
        cfg.LOADER = 'wikimedia_thumbor.loader.proxy'
        cfg.HTTP_LOADER_MAX_BODY_SIZE = 1024*1024*1024  # 1GB
        cfg.PROXY_LOADER_LOADERS = [
            'wikimedia_thumbor.loader.video',
            'wikimedia_thumbor.loader.https'
        ]

        return cfg

    def test_tiff(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:format(jpg)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/0/0e/0729.tiff',
            'lossy-page1-400px-0729.tiff.jpg',
            0.95,
            1.0
        )

    def test_multipage_tiff(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:format(jpg):page(3)/https://'
            + 'upload.wikimedia.org/wikipedia/commons/8/87/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            0.98,
            1.0
        )

    def test_multipage_tiff_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:format(jpg)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/8/87/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.98,
            1.0
        )

    def test_multipage_tiff_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:format(jpg):page(500)/https://'
            + 'upload.wikimedia.org/wikipedia/commons/8/87/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.98,
            1.0
        )

    def test_png(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/c/cf'
            + '/WorldMap-A_non-Frame.png',
            '400px-WorldMap-A_non-Frame.png',
            0.94,
            1.0
        )
