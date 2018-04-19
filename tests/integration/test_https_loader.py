from . import WikimediaTestCase


class WikimediaHttpsLoaderTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaHttpsLoaderTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.proxy'
        cfg.HTTP_LOADER_MAX_BODY_SIZE = 1024*1024*1024  # 1GB
        cfg.HTTP_LOADER_TEMP_FILE_TIMEOUT = 120
        cfg.PROXY_LOADER_LOADERS = [
            'wikimedia_thumbor.loader.video',
            'wikimedia_thumbor.loader.https'
        ]
        cfg.LOADER_EXCERPT_LENGTH = 4096

        return cfg

    def test_huge_djvu(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(440)/https://upload.wikimedia.org/wikipedia/commons/e/ef/Zibaldone_di_pensieri_V.djvu',
            'page440-400px-Zibaldone_di_pensieri_V.djvu.jpg',
            'page440-400px-Zibaldone_di_pensieri_V.djvu.png',
            400,
            712,
            0.95,
            1.06
        )

    def test_jpg(self):
        self.run_and_check_ssim_and_size(
            ('thumbor/unsafe/400x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/'
                'https://upload.wikimedia.org/wikipedia/commons/6/6d/Christophe_Henner_-_June_2016.jpg'),
            '400px-Christophe_Henner_-_June_2016.jpg',
            '400px-Christophe_Henner_-_June_2016.png',
            400,
            267,
            0.92,
            1.02
        )

    def test_png(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/d/d6/1Mcolors.png',
            '400px-1Mcolors.png',
            '400px-1Mcolors.png',
            400,
            400,
            0.99,
            0.74
        )

    def test_tiff(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/0/0e/0729.tiff',
            'lossy-page1-400px-0729.tiff.jpg',
            'lossy-page1-400px-0729.tiff.png',
            400,
            254,
            0.97,
            0.68,
        )

    def test_multipage_tiff(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(3)/https://upload.wikimedia.org/wikipedia/commons/8/87/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            'lossy-page3-400px-All_that_jazz.tif.png',
            400,
            518,
            0.99,
            0.63,
        )

    def test_multipage_tiff_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500)/https://upload.wikimedia.org/wikipedia/commons/8/87/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            'lossy-page1-400px-All_that_jazz.tif.png',
            400,
            518,
            0.99,
            0.69,
        )

    def test_svg(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:lang(fr):format(png)/https://upload.wikimedia.org/wikipedia/commons/3/39/Speech_bubbles.svg',
            'langfr-200px-Speech_bubbles.svg.png',
            'langfr-200px-Speech_bubbles.svg.png',
            200,
            148,
            0.99,
            0.74
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:lang(fr):format(png)/https://upload.wikimedia.org/wikipedia/commons/e/e9/Northumberland_in_England.svg',
            '400px-Northumberland_in_England.svg.png',
            '400px-Northumberland_in_England.svg.png',
            400,
            486,
            1.0,
            0.99
        )

    def test_pdf(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(19)/https://upload.wikimedia.org/wikipedia/commons/d/dc/Jeremy_Bentham%2C_A_Fragment_on_Government_(1891).pdf',
            'page19-400px-Jeremy_Bentham.pdf.jpg',
            'page19-400px-Jeremy_Bentham.pdf.png',
            400,
            673,
            0.96,
            0.54,
        )

    def test_xcf(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/https://upload.wikimedia.org/wikipedia/commons/8/86/Janus.xcf',
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

    def test_gif(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/https://upload.wikimedia.org/wikipedia/commons/f/fb/Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            300,
            187,
            0.98,
            1.11
        )

    def test_question_mark_original(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/https://upload.wikimedia.org/wikipedia/commons/'
            + 'c/c4/Interieur,_overzicht_tijdens_restauratie_%28%3F%29_-_Rolduc_-_20357536_-_RCE.jpg',
            '300px-Interieur.jpg',
            '300px-Interieur.png',
            300,
            299,
            0.94,
            1.0
        )
