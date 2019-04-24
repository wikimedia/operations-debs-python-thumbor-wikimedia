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
            '640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.png',
            640,
            480,
            0.98,
            0.76
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/filters:format(webp)/' + path,
            '640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.jpg',
            '640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.png',
            640,
            480,
            0.97,
            0.49
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
            '320px--Aequipotentialflaechen.webm.png',
            320,
            240,
            0.98,
            0.99
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/320x/filters:format(webp)/' + path,
            '320px--Aequipotentialflaechen.webm.jpg',
            '320px--Aequipotentialflaechen.webm.png',
            320,
            240,
            0.99,
            0.54
        )

        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Cape_Town_under_the_clouds.webm'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/' + path,
            '640px--Cape_Town_under_the_clouds.webm.jpg',
            '640px--Cape_Town_under_the_clouds.webm.png',
            640,
            361,
            0.97,
            0.77
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/filters:format(webp)/' + path,
            '640px--Cape_Town_under_the_clouds.webm.jpg',
            '640px--Cape_Town_under_the_clouds.webm.png',
            640,
            361,
            0.96,
            0.38
        )

        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/' + path,
            '640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.jpg',
            '640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.png',
            640,
            360,
            0.98,
            0.86
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/640x/filters:format(webp)/' + path,
            '640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.jpg',
            '640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.png',
            640,
            360,
            0.98,
            0.48
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
            '320px-seek=1-Aequipotentialflaechen.webm.png',
            320,
            240,
            0.99,
            0.81
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/320x/filters:format(webp):page(1)/' + path,
            '320px-seek=1-Aequipotentialflaechen.webm.jpg',
            '320px-seek=1-Aequipotentialflaechen.webm.png',
            320,
            240,
            0.99,
            0.41
        )

    def test_non_square_pixels(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Malta-cat.ogv'
        )

        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/800x/' + path,
            '800px-Malta-cat.ogv.jpg',
            '800px-Malta-cat.ogv.png',
            800,
            450,
            0.96,
            0.85
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/800x/filters:format(webp)/' + path,
            '800px-Malta-cat.ogv.jpg',
            '800px-Malta-cat.ogv.png',
            800,
            450,
            0.95,
            0.49
        )
