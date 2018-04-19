from . import WikimediaTestCase


class WikimediaHugeVideoTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaHugeVideoTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.video'

        return cfg

    def test_webm_with_fallback_seek(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/320x/filters:page(82)/https://upload.wikimedia.org/wikipedia/commons/a/ab/Borsch_01.webm',
            '320px-seek=0-Borsch_01.webm.jpg',
            '320px-seek=0-Borsch_01.webm.png',
            320,
            180,
            0.96,
            0.93
        )

    def test_404(self):
        url = 'thumbor/unsafe/320x/filters:page(82)/https://upload.wikimedia.org/'\
            'wikipedia/commons/a/ab/Thisfiledoesntexist.webm'

        try:
            result = self.retrieve("/%s" % url)
        except Exception as e:
            assert False, 'Exception occured: %r' % e

        assert result is not None, 'No result'
        assert result.code == 404, 'Response code: %s' % result.code
