import platform

from nose.plugins.skip import SkipTest

from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_png(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/1Mcolors.png',
            '400px-1Mcolors.png',
            '400px-1Mcolors.png',
            400,
            400,
            0.99,
            0.74
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/1Mcolors.png',
            '400px-1Mcolors.png',
            '400px-1Mcolors.png',
            400,
            400,
            0.99,
            0.2
        )

    def test_broken(self):
        # That file only works with recent versions of ImageMagick
        # Our production version doesn't support it yet
        if platform.system() != 'Darwin':
            raise SkipTest

        # T179200 Partially broken PNG
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/Nokia_3310_2017_DS.png',
            '400px-Nokia_3310_2017_DS.png',
            '400px-Nokia_3310_2017_DS.png',
            400,
            901,
            0.99,
            1.1
        )

    def test_transparent(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/' +
            'PNG_transparency_demonstration_1.png',
            '400px-PNG_transparency_demonstration_1.png',
            '400px-PNG_transparency_demonstration_1.png',
            400,
            300,
            0.97,
            1.1
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/filters:format(webp)/' +
            'PNG_transparency_demonstration_1.png',
            '400px-PNG_transparency_demonstration_1.png',
            '400px-PNG_transparency_demonstration_1.png',
            400,
            300,
            # WebP compresses the alpha layer more agressively by default, which results in this
            # low score. This can be avoided in webp >= 0.5 with the -exact function, currently
            # only available on Debian Stretch.
            0.23,
            0.68
        )
        # Palette PNG
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/400x/' +
            'Cincinnati_Bell_logo.png',
            '400px-Cincinnati_Bell_logo.png',
            '400px-Cincinnati_Bell_logo.png',
            400,
            86,
            # Likely due to differences compressing the transparency layer between IM versions
            0.75,
            # The thumbnail is bigger because ImageMagick either messes with the palette if we ask it
            # to generate a palette PNG via the PNG8 output, making the image ugly and aliased (but small)
            # or, as it does automatically here, converts the output to an RGBA image and conserves fidelity
            1.13
        )
