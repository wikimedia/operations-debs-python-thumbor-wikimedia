from . import WikimediaTestCase


class Wikimedia3DTest(WikimediaTestCase):
    def test_stl_text(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/filters:format(png)/crystal-NEW.stl',
            '300px-crystal-NEW.stl.png',
            '300px-crystal-NEW.stl.png',
            300,
            225,
            1,
            1
        )

    def test_stl_bin(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/filters:format(png)/4x2brick_0.00interference.STL',
            '300px-4x2brick_0.00interference.stl.png',
            '300px-4x2brick_0.00interference.stl.png',
            300,
            225,
            1,
            1
        )
