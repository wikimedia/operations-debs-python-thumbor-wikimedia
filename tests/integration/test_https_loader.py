import platform

from . import WikimediaTestCase


class WikimediaHttpsLoaderTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaHttpsLoaderTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.proxy'
        cfg.HTTP_LOADER_MAX_BODY_SIZE = 1024*1024*1024  # 1GB
        cfg.PROXY_LOADER_LOADERS = [
            'wikimedia_thumbor.loader.video',
            'wikimedia_thumbor.loader.https'
        ]

        return cfg

    def test_huge_djvu(self):
        # We have to host this on testwiki because thumbor's default
        # handler doesn't like commas and the original has one in its title
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(440)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/e/ef/Zibaldone_di_pensieri_V.djvu',
            'page440-400px-Zibaldone_di_pensieri_V.djvu.jpg',
            # Mediawiki generates incorrect dimensions in this test case
            # resulting in soft djvu thumbs
            0.71,
            1.2
        )

    def test_jpg(self):
        self.run_and_check_ssim_and_size(
            ('unsafe/400x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/'
                'https://upload.wikimedia.org/wikipedia/commons/'
                + '6/6d/Christophe_Henner_-_June_2016.jpg'),
            '400px-Christophe_Henner_-_June_2016.jpg',
            0.98,
            1.0
        )

    def test_png(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/'
            + 'thumb/d/d6/1Mcolors.png/600px-1Mcolors.png',
            '400px-1Mcolors.png',
            0.99,
            1.0
        )

    def test_tiff(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/'
            + '0/0e/0729.tiff',
            'lossy-page1-400px-0729.tiff.jpg',
            0.96,
            1.0
        )

    def test_multipage_tiff(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(3)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/8/87/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_multipage_tiff_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(500)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/8/87/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_svg(self):
        self.run_and_check_ssim_and_size(
            'unsafe/200x/filters:lang(fr):format(png)/https://'
            + 'upload.wikimedia.org/wikipedia/commons/3/39/Speech_bubbles.svg',
            'langfr-200px-Speech_bubbles.svg.png',
            (0.6 if platform.system() == 'Darwin' else 0.99),
            1.1
        )

    def test_pdf(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(19)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/d/dc/Jeremy_Bentham%2C_A_Fragment_on_'
            + 'Government_(1891).pdf',
            'page19-400px-Jeremy_Bentham.pdf.jpg',
            0.96,
            1.0
        )

    def test_xcf(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:format(png)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/8/86/Janus.xcf',
            '400px-Janus.xcf.png',
            # Compression/sharpening artifacts explain the SSIM difference, but
            # it's impossible to say when eyeballing if one if higher quality
            # than the other
            0.92,
            1.01
        )
