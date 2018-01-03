import os

from . import WikimediaTestCase


class WikimediaVideoTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaVideoTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.video'

        return cfg

    def test_ogv(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            '2010-07-14-Blitze-Zeitlupe-1-08.ogg'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/' + path,
            '640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.jpg',
            0.99,
            1.0
        )

    def test_webm(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Aequipotentialflaechen.webm'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/320x/' + path,
            '320px--Aequipotentialflaechen.webm.jpg',
            0.99,
            1.0
        )

        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Cape_Town_under_the_clouds.webm'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/' + path,
            '640px--Cape_Town_under_the_clouds.webm.jpg',
            0.98,
            1.0
        )

        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/' + path,
            '640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.jpg',
            0.99,
            1.0
        )

    def test_webm_with_seek(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Aequipotentialflaechen.webm'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/320x/filters:page(1)/' + path,
            '320px-seek=1-Aequipotentialflaechen.webm.jpg',
            0.99,
            1.0
        )
