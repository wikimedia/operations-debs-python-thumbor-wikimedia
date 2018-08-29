from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_xcf(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Janus.xcf',
            '400px-Janus.xcf.png',
            '400px-Janus.xcf.png',
            400,
            431,
            # Compression/sharpening artifacts explain the SSIM difference, but
            # it's impossible to say when eyeballing if one if higher quality
            # than the other
            0.92,
            1.01
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/Janus.xcf',
            '400px-Janus.xcf.png',
            '400px-Janus.xcf.png',
            400,
            431,
            0.92,
            0.68
        )
