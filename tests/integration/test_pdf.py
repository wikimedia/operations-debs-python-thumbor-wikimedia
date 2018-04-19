from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_pdf(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(3)/Internationalisation.pdf',
            'page3-400px-Internationalisation.pdf.jpg',
            'page3-400px-Internationalisation.pdf.png',
            400,
            300,
            0.92,
            0.55,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(3):format(webp)/Internationalisation.pdf',
            'page3-400px-Internationalisation.pdf.jpg',
            'page3-400px-Internationalisation.pdf.png',
            400,
            300,
            0.93,
            0.62,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(19)/Jeremy_Bentham.pdf',
            'page19-400px-Jeremy_Bentham.pdf.jpg',
            'page19-400px-Jeremy_Bentham.pdf.png',
            400,
            673,
            0.96,
            0.54,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(19):format(webp)/Jeremy_Bentham.pdf',
            'page19-400px-Jeremy_Bentham.pdf.jpg',
            'page19-400px-Jeremy_Bentham.pdf.png',
            400,
            673,
            0.98,
            0.42,
        )

    def test_pdf_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.92,
            0.54,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.93,
            0.6,
        )

    def test_pdf_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.92,
            0.54,
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:page(500):format(webp)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.93,
            0.6,
        )
