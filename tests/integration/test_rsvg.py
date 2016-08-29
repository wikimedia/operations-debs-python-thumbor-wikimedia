import platform

from thumbor.utils import which

from . import WikimediaTestCase


class WikimediaRSVGTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaRSVGTest, self).get_config()
        cfg.RSVG_CONVERT_PATH = which('rsvg-convert')
        return cfg

    def test_rsvg(self):
        self.run_and_check_ssim_and_size(
            'unsafe/200x/filters:lang(fr):format(png)/Speech_bubbles.svg',
            'langfr-200px-Speech_bubbles.svg.png',
            # Low score on OS X due to font differences
            (0.6 if platform.system() == 'Darwin' else 0.99),
            1.00
        )
