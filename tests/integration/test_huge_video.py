from . import WikimediaTestCase


class WikimediaHugeVideoTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaHugeVideoTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.video'

        return cfg

    def test_webm_with_fallback_seek(self):
        self.run_and_check_ssim_and_size(
            'unsafe/320x/filters:page(82)/https://upload.wikimedia.org/'
            + 'wikipedia/commons/a/ab/Borsch_01.webm',
            '320px-seek=0-Borsch_01.webm.jpg',
            0.98,
            1.0
        )
