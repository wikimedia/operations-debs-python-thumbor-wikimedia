from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    def test_gif(self):
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            '300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            300,
            187,
            0.98,
            1.11
        )
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Jokie.gif',
            '300px-Jokie.gif',
            '300px-Jokie.gif',
            300,
            290,
            1.0,
            1.11
        )
        # Animated GIF that triggers MAX_ANIMATED_GIF_AREA
        self.run_and_check_ssim_and_size(
            'thumbor/unsafe/300x/Tranylcypromine3DanJ.gif',
            '300px-Tranylcypromine3DanJ.gif',
            '300px-Tranylcypromine3DanJ.gif',
            300,
            145,
            1.0,
            1.0
        )
