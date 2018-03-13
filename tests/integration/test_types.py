import platform

from nose.plugins.skip import SkipTest

from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_jpg(self):
        self.run_and_check_ssim_and_size(
            ('thumbor/unsafe/400x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/'
                'Christophe_Henner_-_June_2016.JPG'),
            '400px-Christophe_Henner_-_June_2016.jpg',
            0.98,
            1.0
        )

    def test_djvu(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(2)/Il_cavallarizzo.djvu',
            'page2-400px-Il_cavallarizzo.djvu.jpg',
            # Mediawiki generates incorrect dimensions in this test case
            # resulting in soft djvu thumbs
            0.88,
            1.1
        )

    def test_djvu_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/Il_cavallarizzo.djvu',
            'page1-400px-Il_cavallarizzo.djvu.jpg',
            # Mediawiki generates incorrect dimensions in this test case
            # resulting in soft djvu thumbs
            0.87,
            1.2
        )

    def test_djvu_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500)/Il_cavallarizzo.djvu',
            'page259-400px-Il_cavallarizzo.djvu.jpg',
            # Mediawiki generates incorrect dimensions in this test case
            # resulting in soft djvu thumbs
            0.87,
            1.1
        )

    def test_svg(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:lang(fr):format(png)/Speech_bubbles.svg',
            'langfr-200px-Speech_bubbles.svg.png',
            (0.6 if platform.system() == 'Darwin' else 0.99),
            1.1
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:format(png)/Television.svg',
            '200px-Television.svg.png',
            # This file is only there to test SVG syntax
            0.36,
            1.1
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:format(png)/Lori_in_Armenia.svg',
            '200px-Lori_in_Armenia.svg.png',
            0.94,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Northumberland_in_England.svg',
            '400px-Northumberland_in_England.svg.png',
            1.0,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Map_of_the_Beboid_languages.svg',
            '400px-Map_of_the_Beboid_languages.svg.png',
            0.99,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Westmoreland_Heritage_Trail.svg',
            '400px-Westmoreland_Heritage_Trail.svg.png',
            1.0,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Tree_edges.svg',
            '400px-Tree_edges.svg.png',
            0.99,
            1.2
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/119x/filters:format(png)/BuickLogo_silber.svg',
            '119px-BuickLogo_silber.svg.png',
            1.0,
            1.0
        )

    def test_pdf(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(3)/Internationalisation.pdf',
            'page3-400px-Internationalisation.pdf.jpg',
            # Low score because framing is slightly different, and includes
            # more content in the Thumbor case
            0.87,
            1.0
        )

    def test_pdf2(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(19)/Jeremy_Bentham.pdf',
            'page19-400px-Jeremy_Bentham.pdf.jpg',
            0.96,
            1.0
        )

    def test_pdf_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            # Low score because framing is slightly different, and includes
            # more content in the Thumbor case
            0.86,
            1.0
        )

    def test_pdf_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            # Low score because framing is slightly different, and includes
            # more content in the Thumbor case
            0.86,
            1.0
        )

    def test_xcf(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Janus.xcf',
            '400px-Janus.xcf.png',
            # Compression/sharpening artifacts explain the SSIM difference, but
            # it's impossible to say when eyeballing if one if higher quality
            # than the other
            0.92,
            1.01
        )

    def test_tiff(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/0729.tiff',
            'lossy-page1-400px-0729.tiff.jpg',
            0.96,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Lejeune.TIF',
            'lossy-page1-300px-Lejeune.TIF.jpg',
            0.97,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Hafnia_alvei.tif',
            'lossy-page1-300px-Hafnia_alvei.tif.jpg',
            0.96,
            1.0
        )

    def test_multipage_tiff(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(3)/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_multipage_tiff_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_multipage_tiff_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_png(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/1Mcolors.png',
            '400px-1Mcolors.png',
            0.99,
            1.0
        )

    def test_broken_png(self):
        # That file only works with recent versions of ImageMagick
        # Our production version doesn't support it yet
        raise SkipTest
        # T179200 Partially broken PNG
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/Nokia_3310_2017_DS.png',
            '400px-Nokia_3310_2017_DS.png',
            0.99,
            1.1
        )

    def test_crop(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:crop(10,10,20,20)/1Mcolors.png',
            'crop-1Mcolors.png',
            0.99,
            1.0
        )

    def test_flip_x(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:flip(x)/1Mcolors.png',
            'flipx-1Mcolors.png',
            0.99,
            1.0
        )

    def test_flip_y(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:flip(y)/1Mcolors.png',
            'flipy-1Mcolors.png',
            0.99,
            1.0
        )

    def test_rotate(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/filters:rotate(90)/1Mcolors.png',
            'rot90deg-1Mcolors.png',
            0.99,
            1.0
        )

    def test_transparent_png(self):
        # We add a no-op filter to trigger image_data_as_rgb on an RGBA image
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:conditional_sharpen(0.0,0.0,0.0,0.0,0.0)/' +
            'PNG_transparency_demonstration_1.png',
            '400px-PNG_transparency_demonstration_1.png',
            0.97,
            1.1
        )

    def test_gif(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            0.98,
            1.1
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Jokie.gif',
            '300px-Jokie.gif',
            1.0,
            1.1
        )
        # Animated GIF that triggers MAX_ANIMATED_GIF_AREA
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Tranylcypromine3DanJ.gif',
            '300px-Tranylcypromine3DanJ.gif',
            1.0,
            1.0
        )

    def test_webp(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/filters:format(png)/Album_en_blanco_y_negro.webp',
            '300px-Album_en_blanco_y_negro.webp.png',
            0.99,
            1.1
        )
