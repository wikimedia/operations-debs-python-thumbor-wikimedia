import os
import subprocess
import tempfile
import PIL.ExifTags

from . import WikimediaTestCase


class WikimediaExifTest(WikimediaTestCase):
    def run_and_check_ssim_size_and_exif(
        self,
        url,
        expected,
        expected_ssim,
        size_tolerance,
        expected_exif_fields,
        expected_icc_profile
    ):
        """Request URL and check ssim, size and exif.

        Arguments:
        url -- thumbnail URL
        expected -- reference thumbnail file
        expected_ssim -- minimum SSIM score
        size_tolerance -- maximum file size ratio between reference and result
        expected_exif_fields -- expected EXIF field values
        expected_icc_profile -- expected ICC profile
        """
        result = super(WikimediaExifTest, self).run_and_check_ssim_and_size(
            url,
            expected,
            expected_ssim,
            size_tolerance
        )

        if expected_exif_fields:
            self.check_exif(result, expected_exif_fields)

        if expected_icc_profile:
            assert result.info['icc_profile'] == expected_icc_profile, \
                'ICC profile: %s' % result.info['icc_profile']

    def check_exif(self, image, exif_fields):
        exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in image._getexif().items()
            if k in PIL.ExifTags.TAGS
        }

        for field in exif_fields:
            reference = exif_fields[field]
            result = exif[field]
            assert result == reference, \
                'EXIF field %s: %s' % (field, result)

    def test_adobe_rgb(self):
        self.run_and_check_ssim_size_and_exif(
            'unsafe/300x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/'
            + 'Physical_map_tagged_AdobeRGB.jpg',
            '300px-Physical_map_tagged_AdobeRGB.jpg',
            0.97,
            1.0,
            None,
            '\x00\x00\x02HADBE\x02\x10\x00\x00mntrRGB XYZ \x07\xcf\x00\x06\x00'
            + '\x03\x00\x00\x00\x00\x00\x00acspMSFT\x00\x00\x00\x00none\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
            + '\x00\x00\xf6\xd6\x00\x01\x00\x00\x00\x00\xd3-ADBE\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\ncprt\x00\x00\x00\xfc\x00\x00\x00Ldesc\x00\x00\x01H\x00\x00'
            + '\x00kwtpt\x00\x00\x01\xb4\x00\x00\x00\x14bkpt\x00\x00\x01\xc8'
            + '\x00\x00\x00\x14rTRC\x00\x00\x01\xdc\x00\x00\x00\x0egTRC\x00'
            + '\x00\x01\xec\x00\x00\x00\x0ebTRC\x00\x00\x01\xfc\x00\x00\x00'
            + '\x0erXYZ\x00\x00\x02\x0c\x00\x00\x00\x14gXYZ\x00\x00\x02 \x00'
            + '\x00\x00\x14bXYZ\x00\x00\x024\x00\x00\x00\x14text\x00\x00\x00'
            + '\x00Copyright (c) 1999 Adobe Systems Incorporated. All Rights '
            + 'Reserved.\x00desc\x00\x00\x00\x00\x00\x00\x00\x11Adobe RGB '
            + '(1998)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00XYZ \x00\x00\x00\x00\x00\x00\xf3Q\x00'
            + '\x01\x00\x00\x00\x01\x16\xccXYZ \x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00curv\x00\x00\x00\x00\x00'
            + '\x00\x00\x01\x023\x00\x00curv\x00\x00\x00\x00\x00\x00\x00\x01'
            + '\x023\x00\x00curv\x00\x00\x00\x00\x00\x00\x00\x01\x023\x00'
            + '\x00XYZ \x00\x00\x00\x00\x00\x00\x9c\x18\x00\x00O\xa5\x00\x00'
            + '\x04\xfcXYZ \x00\x00\x00\x00\x00\x004\x8d\x00\x00\xa0,\x00\x00'
            + '\x0f\x95XYZ \x00\x00\x00\x00\x00\x00&1\x00\x00\x10/\x00\x00'
            + '\xbe\x9c'
        )

    def test_exif_filtering(self):
        self.run_and_check_ssim_size_and_exif(
            'unsafe/800x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/'
            + 'Munich_subway_station_Westfriedhof.jpg',
            '800px-Munich_subway_station_Westfriedhof.jpg',
            0.97,
            1.1,
            {
                'Artist': 'Martin Falbisoner',
                'Copyright': 'some rights reserved'
            },
            None
        )

    def test_exif_rotation(self):
        self.run_and_check_ssim_size_and_exif(
            'unsafe/40x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/'
            + 'EXIF_rotation_180.jpg',
            '40px-EXIF_rotation_180.jpg',
            0.99,
            1.1,
            None,
            None
        )

    def test_tinyrgb_substitution(self):
        tinyrgb_path = os.path.join(
            os.path.dirname(__file__),
            'tinyrgb.icc'
        )
        with open(tinyrgb_path, 'r') as tinyrgb_file:
            tinyrgb = tinyrgb_file.read()

        self.run_and_check_ssim_size_and_exif(
            'unsafe/400x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/'
            + 'Christophe_Henner_-_June_2016.JPG',
            '400px-Christophe_Henner_-_June_2016.jpg',
            0.98,
            1.0,
            None,
            tinyrgb
        )
