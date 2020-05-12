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
            'lossy-page1-400px-0729.tiff.png',
            400,
            254,
            0.95,
            0.61,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/0729.tiff',
            'lossy-page1-400px-0729.tiff.jpg',
            'lossy-page1-400px-0729.tiff.png',
            400,
            254,
            0.98,
            1.12,
        )

    def test_multipage_tiff(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(jpg):page(3)/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            'lossy-page3-400px-All_that_jazz.tif.png',
            400,
            518,
            0.98,
            0.6,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp):page(3)/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            'lossy-page3-400px-All_that_jazz.tif.png',
            400,
            518,
            0.99,
            0.68,
        )

    def test_multipage_tiff_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(jpg)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            'lossy-page1-400px-All_that_jazz.tif.png',
            400,
            518,
            0.99,
            0.63,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            'lossy-page1-400px-All_that_jazz.tif.png',
            400,
            518,
            0.99,
            0.61,
        )

    def test_multipage_tiff_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(jpg):page(500)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            'lossy-page1-400px-All_that_jazz.tif.png',
            400,
            518,
            0.99,
            0.63,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp):page(500)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            'lossy-page1-400px-All_that_jazz.tif.png',
            400,
            518,
            0.99,
            0.61,
        )

    def test_tiff_with_invalid_icc_profile(self):
        self.run_and_check_ssim_and_size(
            (
                'thumbor/unsafe/400x/filters:format(jpg)/Julia_Margaret_'
                'Cameron_-_Queen_of_the_May_-_1984.166_-_Cleveland_Museum_of_Art.tif'
            ),
            (
                'lossy-page1-400px-Julia_Margaret_Cameron_-_Queen_of_the_May_'
                '-_1984.166_-_Cleveland_Museum_of_Art.tif.jpg'
            ),
            (
                'lossy-page1-400px-Julia_Margaret_Cameron_-_Queen_of_the_May_'
                '-_1984.166_-_Cleveland_Museum_of_Art.tif.png'
            ),
            400,
            527,
            0.97,
            0.6,
        )
        self.run_and_check_ssim_and_size(
            (
                'thumbor/unsafe/400x/filters:format(webp)/Julia_Margaret_'
                'Cameron_-_Queen_of_the_May_-_1984.166_-_Cleveland_Museum_of_Art.tif'
            ),
            (
                'lossy-page1-400px-Julia_Margaret_Cameron_-_Queen_of_the_May_'
                '-_1984.166_-_Cleveland_Museum_of_Art.tif.webp'
            ),
            (
                'lossy-page1-400px-Julia_Margaret_Cameron_-_Queen_of_the_May_'
                '-_1984.166_-_Cleveland_Museum_of_Art.tif.png'
            ),
            400,
            527,
            0.97,
            1.0,
        )

    def test_png(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/WorldMap-A_non-Frame.png',
            '400px-WorldMap-A_non-Frame.png',
            '400px-WorldMap-A_non-Frame.png',
            400,
            200,
            0.94,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/WorldMap-A_non-Frame.png',
            '400px-WorldMap-A_non-Frame.png',
            '400px-WorldMap-A_non-Frame.png',
            400,
            200,
            0.98,
            0.84
        )
