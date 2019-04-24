import platform
from . import WikimediaTestCase


distname, distversion, distid = platform.linux_distribution()
distversion = 10.0 if distversion == 'buster/sid' else float(distversion)


class WikimediaTest(WikimediaTestCase):
    def test_svg(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:lang(fr):format(png)/Speech_bubbles.svg',
            'langfr-200px-Speech_bubbles.svg.png',
            'langfr-200px-Speech_bubbles.svg.png',
            200,
            148,
            0.99,
            0.74
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:lang(fr):format(webp)/Speech_bubbles.svg',
            'langfr-200px-Speech_bubbles.svg.png',
            'langfr-200px-Speech_bubbles.svg.png',
            200,
            148,
            0.99,
            0.48
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:format(png)/Television.svg',
            '200px-Television.svg.png',
            '200px-Television.svg.png',
            200,
            200,
            0.99,
            0.96
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:format(webp)/Television.svg',
            '200px-Television.svg.png',
            '200px-Television.svg.png',
            200,
            200,
            # WebP compresses the alpha layer more agressively by default, which results in this
            # low score. This can be avoided in webp >= 0.5 with the -exact function, currently
            # only available on Debian Stretch.
            0.99 if distname == 'debian' and distversion >= 9 else 0.81,
            0.66
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:format(png)/Lori_in_Armenia.svg',
            '200px-Lori_in_Armenia.svg.png',
            '200px-Lori_in_Armenia.svg.png',
            200,
            205,
            0.94,
            0.98
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/200x/filters:format(webp)/Lori_in_Armenia.svg',
            '200px-Lori_in_Armenia.svg.png',
            '200px-Lori_in_Armenia.svg.png',
            200,
            205,
            0.94,
            0.5
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Northumberland_in_England.svg',
            '400px-Northumberland_in_England.svg.png',
            '400px-Northumberland_in_England.svg.png',
            400,
            486,
            1.0,
            0.99
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/Northumberland_in_England.svg',
            '400px-Northumberland_in_England.svg.png',
            '400px-Northumberland_in_England.svg.png',
            400,
            486,
            1.0,
            0.5
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Map_of_the_Beboid_languages.svg',
            '400px-Map_of_the_Beboid_languages.svg.png',
            '400px-Map_of_the_Beboid_languages.svg.png',
            400,
            249,
            0.99,
            1.0
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/Map_of_the_Beboid_languages.svg',
            '400px-Map_of_the_Beboid_languages.svg.png',
            '400px-Map_of_the_Beboid_languages.svg.png',
            400,
            249,
            0.99,
            0.86
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Westmoreland_Heritage_Trail.svg',
            '400px-Westmoreland_Heritage_Trail.svg.png',
            '400px-Westmoreland_Heritage_Trail.svg.png',
            400,
            161,
            1.0,
            0.99
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/Westmoreland_Heritage_Trail.svg',
            '400px-Westmoreland_Heritage_Trail.svg.png',
            '400px-Westmoreland_Heritage_Trail.svg.png',
            400,
            161,
            1.0,
            0.63
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(png)/Tree_edges.svg',
            '400px-Tree_edges.svg.png',
            '400px-Tree_edges.svg.png',
            400,
            238,
            0.99,
            1.2
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/Tree_edges.svg',
            '400px-Tree_edges.svg.png',
            '400px-Tree_edges.svg.png',
            400,
            238,
            0.99,
            0.73
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/119x/filters:format(png)/BuickLogo_silber.svg',
            '119px-BuickLogo_silber.svg.png',
            '119px-BuickLogo_silber.svg.png',
            119,
            120,
            0.99,
            0.99
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/119x/filters:format(webp)/BuickLogo_silber.svg',
            '119px-BuickLogo_silber.svg.png',
            '119px-BuickLogo_silber.svg.png',
            119,
            120,
            # WebP compresses the alpha layer more agressively by default, which results in this
            # low score. This can be avoided in webp >= 0.5 with the -exact function, currently
            # only available on Debian Stretch.
            0.99 if distname == 'debian' and distversion >= 9 else 0.63,
            0.67
        )
