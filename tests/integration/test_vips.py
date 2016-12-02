from . import WikimediaTestCase


class WikimediaVipsTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaVipsTest, self).get_config()
        cfg.VIPS_ENGINE_MIN_PIXELS = 0

        return cfg

    def test_tiff(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(jpg)/0729.tiff',
            'lossy-page1-400px-0729.tiff.jpg',
            0.95,
            1.0
        )

    def test_multipage_tiff(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(jpg):page(3)/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            0.98,
            1.0
        )

    def test_multipage_tiff_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(jpg)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.98,
            1.0
        )

    def test_multipage_tiff_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(jpg):page(500)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.98,
            1.0
        )

    def test_png(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/WorldMap-A_non-Frame.png',
            '400px-WorldMap-A_non-Frame.png',
            0.94,
            1.0
        )
