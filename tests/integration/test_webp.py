from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_webp(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/filters:format(png)/Album_en_blanco_y_negro.webp',
            '300px-Album_en_blanco_y_negro.webp.png',
            '300px-Album_en_blanco_y_negro.webp.png',
            300,
            202,
            0.99,
            1.06
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/filters:format(webp)/Album_en_blanco_y_negro.webp',
            '300px-Album_en_blanco_y_negro.webp.png',
            '300px-Album_en_blanco_y_negro.webp.png',
            300,
            202,
            0.97,
            0.14
        )
