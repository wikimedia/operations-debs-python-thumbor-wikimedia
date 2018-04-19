from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_crop(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:crop(10,10,20,20)/1Mcolors.png',
            'crop-1Mcolors.png',
            'crop-1Mcolors.png',
            10,
            10,
            0.98,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:crop(10,10,20,20):format(webp)/1Mcolors.png',
            'crop-1Mcolors.png',
            'crop-1Mcolors.png',
            10,
            10,
            0.98,
            0.25
        )

    def test_flip_x(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:flip(x)/1Mcolors.png',
            'flipx-1Mcolors.png',
            'flipx-1Mcolors.png',
            400,
            400,
            0.99,
            0.89
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:flip(x):format(webp)/1Mcolors.png',
            'flipx-1Mcolors.png',
            'flipx-1Mcolors.png',
            400,
            400,
            0.99,
            0.22
        )

    def test_flip_y(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:flip(y)/1Mcolors.png',
            'flipy-1Mcolors.png',
            'flipy-1Mcolors.png',
            400,
            400,
            0.99,
            0.87
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:flip(y):format(webp)/1Mcolors.png',
            'flipy-1Mcolors.png',
            'flipy-1Mcolors.png',
            400,
            400,
            0.99,
            0.22
        )

    def test_rotate(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/filters:rotate(90)/1Mcolors.png',
            'rot90deg-1Mcolors.png',
            'rot90deg-1Mcolors.png',
            1000,
            1000,
            0.99,
            0.4
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/filters:rotate(90):format(webp)/1Mcolors.png',
            'rot90deg-1Mcolors.png',
            'rot90deg-1Mcolors.png',
            1000,
            1000,
            0.99,
            0.04
        )

    def test_no_filter(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/1Mcolors.png',
            '1Mcolors.png',
            '1Mcolors.png',
            1000,
            1000,
            1.0,
            1.5
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/filters:format(webp)/1Mcolors.png',
            '1Mcolors.png',
            '1Mcolors.png',
            1000,
            1000,
            1.0,
            0.18
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/Tower.jpg',
            'Tower.jpg',
            'Tower.jpg',
            1456,
            2592,
            0.98,
            0.53
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/filters:format(webp)/Tower.jpg',
            'Tower.jpg',
            'Tower.jpg',
            1456,
            2592,
            0.97,
            0.37
        )
