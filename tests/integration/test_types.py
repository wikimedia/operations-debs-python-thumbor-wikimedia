from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_jpg(self):
        self.run_and_check_ssim_and_size(
            ('unsafe/400x/filters:conditional_sharpen(0.6,0.01,false,0.85)/'
                'Christophe_Henner_-_June_2016.jpg'),
            '400px-Christophe_Henner_-_June_2016.jpg',
            0.98,
            1.0
        )

    def test_djvu(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(2)/Il_cavallarizzo.djvu',
            'page2-400px-Il_cavallarizzo.djvu.jpg',
            # Mediawiki generates incorrect dimensions in this test case
            # resulting in soft djvu thumbs
            0.88,
            1.0
        )

    def test_djvu_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/Il_cavallarizzo.djvu',
            'page1-400px-Il_cavallarizzo.djvu.jpg',
            # Mediawiki generates incorrect dimensions in this test case
            # resulting in soft djvu thumbs
            0.87,
            1.1
        )

    def test_djvu_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(500)/Il_cavallarizzo.djvu',
            'page1-400px-Il_cavallarizzo.djvu.jpg',
            # Mediawiki generates incorrect dimensions in this test case
            # resulting in soft djvu thumbs
            0.87,
            1.1
        )

    def test_svg(self):
        self.run_and_check_ssim_and_size(
            'unsafe/200x/filters:lang(fr):format(png)/Speech_bubbles.svg',
            'langfr-200px-Speech_bubbles.svg.png',
            # Low score due to font differences
            0.76,
            1.1
        )

    def test_pdf(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(3)/Internationalisation.pdf',
            'page3-400px-Internationalisation.pdf.jpg',
            0.95,
            1.0
        )

    def test_pdf_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            0.95,
            1.0
        )

    def test_pdf_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(500)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            0.95,
            1.0
        )

    def test_xcf(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:format(png)/Janus.xcf',
            '400px-Janus.xcf.png',
            # Compression/sharpening artifacts explain the SSIM difference, but
            # it's impossible to say when eyeballing if one if higher quality
            # than the other
            0.92,
            1.01
        )

    def test_tiff(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/0729.tiff',
            'lossy-page1-400px-0729.tiff.jpg',
            0.96,
            1.0
        )

    def test_multipage_tiff(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(3)/All_that_jazz.tif',
            'lossy-page3-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_multipage_tiff_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_multipage_tiff_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:page(500)/All_that_jazz.tif',
            'lossy-page1-400px-All_that_jazz.tif.jpg',
            0.99,
            1.0
        )

    def test_png(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/1Mcolors.png',
            '400px-1Mcolors.png',
            0.99,
            1.0
        )

    def test_crop(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:crop(10,10,20,20)/1Mcolors.png',
            'crop-1Mcolors.png',
            0.99,
            1.0
        )

    def test_flip_x(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:flip(x)/1Mcolors.png',
            'flipx-1Mcolors.png',
            0.99,
            1.0
        )

    def test_flip_y(self):
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:flip(y)/1Mcolors.png',
            'flipy-1Mcolors.png',
            0.99,
            1.0
        )

    def test_rotate(self):
        self.run_and_check_ssim_and_size(
            'unsafe/filters:rotate(90)/1Mcolors.png',
            'rot90deg-1Mcolors.png',
            0.99,
            1.0
        )

    def test_transparent_png(self):
        # We add a no-op filter to trigger image_data_as_rgb on an RGBA image
        self.run_and_check_ssim_and_size(
            'unsafe/400x/filters:conditional_sharpen(0.0,0.0,false,0.0)/' +
            'PNG_transparency_demonstration_1.png',
            '400px-PNG_transparency_demonstration_1.png',
            0.99,
            1.1
        )
