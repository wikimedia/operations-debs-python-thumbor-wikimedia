from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_with_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(2)/Il_cavallarizzo.djvu',
            'page2-400px-Il_cavallarizzo.djvu.jpg',
            'page2-400px-Il_cavallarizzo.djvu.png',
            400,
            576,
            0.99,
            1.01,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(2):format(webp)/Il_cavallarizzo.djvu',
            'page2-400px-Il_cavallarizzo.djvu.jpg',
            'page2-400px-Il_cavallarizzo.djvu.png',
            400,
            576,
            0.99,
            0.84,
        )

    def test_without_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/Il_cavallarizzo.djvu',
            'page1-400px-Il_cavallarizzo.djvu.jpg',
            'page1-400px-Il_cavallarizzo.djvu.png',
            400,
            561,
            0.98,
            1.11,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/Il_cavallarizzo.djvu',
            'page1-400px-Il_cavallarizzo.djvu.jpg',
            'page1-400px-Il_cavallarizzo.djvu.png',
            400,
            561,
            0.99,
            0.9,
        )

    def test_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500)/Il_cavallarizzo.djvu',
            'page259-400px-Il_cavallarizzo.djvu.jpg',
            'page259-400px-Il_cavallarizzo.djvu.png',
            400,
            619,
            0.99,
            1.05,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500):format(webp)/Il_cavallarizzo.djvu',
            'page259-400px-Il_cavallarizzo.djvu.jpg',
            'page259-400px-Il_cavallarizzo.djvu.png',
            400,
            619,
            0.99,
            0.84,
        )
