#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# ImageMagick engine

from tempfile import NamedTemporaryFile
import wand.image as image
from wand.api import library, ctypes

from thumbor.utils import logger
from thumbor.engines import BaseEngine

from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.exiftool_runner import ExiftoolRunner

image.OPTIONS = frozenset(
    ['fill', 'jpeg:sampling-factor', 'pdf:use-cropbox', 'jpeg:size']
)

# wand doesn't support reading pixel blobs out of the box,
# only file blobs, so we have to monkey-patch that in

library.MagickConstituteImage.argtypes = [
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_size_t,
    ctypes.c_char_p,
    ctypes.c_uint,
    ctypes.c_void_p
]

# similarly, wand doesn't support setting the interlacing scheme

library.MagickSetInterlaceScheme.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
]

ALPHA_TYPES = (
    'grayscalematte',
    'palettematte',
    'truecolormatte'
)

INTERLACE_SCHEMES = (
    'NoInterlace',
    'LineInterlace',
    'PlaneInterlace',
    'PartitionInterlace'
)


def read_blob(self, blob, format, width, height):
    r = library.MagickConstituteImage(
        self.wand,
        int(width),
        int(height),
        format.upper(),
        int(1),
        blob
    )

    if not r:
        self.raise_exception()


def set_interlace_scheme(self, scheme):
    try:
        s = INTERLACE_SCHEMES.index(scheme)
    except IndexError:
        raise IndexError(
            repr(scheme) + ' is an invalid interlace scheme')

    r = library.MagickSetInterlaceScheme(
        self.wand,
        s
    )

    if not r:
        self.raise_exception()

image.Image.read_blob = read_blob
image.Image.set_interlace_scheme = set_interlace_scheme


class Engine(BaseEngine):
    exiftool = ExiftoolRunner()

    def create_image(self, buffer):
        self.im_original_buffer = buffer
        self.exif = {}

        im = image.Image()

        # Read EXIF data from buffer first. This will get us the
        # size if we need it for the jpeg:size option, as well as the
        # ICC profile name in case we need to do profile swapping and
        # the various EXIF fields we want to keep
        if self.extension == '.jpg':
            self.read_exif(buffer)
            if 'ImageSize' in self.exif:
                im.options['jpeg:size'] = self.exif['ImageSize']
                logger.debug('[IM] Set jpeg:size hint')
            else:
                logger.debug('[IM] Failed to read EXIF ImageSize')

        im.read(blob=buffer)

        return im

    def read_exif(self, buffer):
        fields = [
            'ImageSize',
            'ProfileDescription',
        ]

        fields += self.context.config.EXIF_FIELDS_TO_KEEP

        command = [
            '-s',
            '-s',
            '-s',
        ]

        command += ['-{0}'.format(i) for i in fields]

        stdout = Engine.exiftool.command(
            pre=command,
            context=self.context,
            buffer=buffer
        )

        i = 0

        for s in stdout.splitlines():
            field = fields[i]
            self.exif[field] = s
            i += 1

        logger.debug('[IM] EXIF: %r' % self.exif)

        # If we encounter any non-sRGB ICC profile, we save it to re-apply
        # it to the result

        if 'ProfileDescription' not in self.exif:
            logger.debug('[IM] File has no ICC profile')
            return

        expected_profile = self.context.config.EXIF_TINYRGB_ICC_REPLACE.lower()
        profile = self.exif['ProfileDescription'].lower()

        if profile == expected_profile:
            self.icc_profile_path = self.context.config.EXIF_TINYRGB_PATH
            logger.debug('[IM] File has sRGB profile')
            return

        logger.debug('[IM] File has non-sRGB profile')

        command = [
            '-icc_profile',
            '-b',
            '-m',
        ]

        stdout = Engine.exiftool.command(
            pre=command,
            context=self.context,
            buffer=buffer
        )

        profile_file = NamedTemporaryFile(delete=False)
        profile_file.write(stdout)
        profile_file.close()

        self.icc_profile_path = profile_file.name

    def process_exif(self, buffer):
        command = [
            '-m',
            '-all=',  # Strip all existing metadata
        ]

        # Copy the ICC profile
        if hasattr(self, 'icc_profile_path'):
            command += ['-icc_profile<=%s' % self.icc_profile_path]

        for field in self.context.config.EXIF_FIELDS_TO_KEEP:
            if field in self.exif:
                value = self.exif[field]
                command += ['-%s=%s' % (field, value)]

        postCommand = [
            '-o',
            '-'  # Write to stdout
        ]

        stdout = Engine.exiftool.command(
            pre=command,
            post=postCommand,
            context=self.context,
            buffer=buffer
        )

        tinyrgb_path = self.context.config.EXIF_TINYRGB_PATH

        # Clean up saved non-sRGB profile if needed
        if (hasattr(self, 'icc_profile_path')
                and self.icc_profile_path != tinyrgb_path):
            ShellRunner.rm_f(self.icc_profile_path)

        return stdout

    def read(self, extension=None, quality=None):
        if quality is None:
            return self.im_original_buffer

        self.image.compression_quality = quality

        config = self.context.config

        if hasattr(config, 'CHROMA_SUBSAMPLING') and config.CHROMA_SUBSAMPLING:
            self.image.options['jpeg:sampling-factor'] \
                = config.CHROMA_SUBSAMPLING

        logger.debug('[IM] Generating image with quality %r' % quality)

        extension = extension.lstrip('.')

        if extension == 'jpg' and self.context.config.PROGRESSIVE_JPEG:
            self.image.set_interlace_scheme('PlaneInterlace')

        result = self.image.make_blob(format=extension)

        if extension == 'jpg':
            result = self.process_exif(result)

        return result

    def crop(self, crop_left, crop_top, crop_right, crop_bottom):
        # Sometimes thumbor's resize algorithm will try to pre-crop
        # the image. However that gets in the way of the jpeg:size
        # optimization. I presume Thumbor does that to reduce interpolation
        # but it does so at the expense of cutting off one edge of the image
        if not hasattr(self, 'buffer'):
            self.image.crop(
                left=int(crop_left),
                top=int(crop_top),
                right=int(crop_right),
                bottom=int(crop_bottom)
            )

    def resize(self, width, height):
        self.image.resize(width=int(width), height=int(height))

    def flip_horizontally(self):
        self.image.flop()

    def flip_vertically(self):
        self.image.flip()

    def rotate(self, degrees):
        self.image.rotate(degree=degrees)

    def reorientate(self):
        # We can't reorientate right now because we have no image
        if hasattr(self, 'buffer'):
            return

        self.image.auto_orient()

    def image_data_as_rgb(self, update_image=True):
        converted = self.image.convert(self.mode)

        if update_image:
            self.image = converted

        return self.mode, converted.make_blob()

    def set_image_data(self, data):
        width, height = self.image.size

        rgb = image.Image()
        rgb.read_blob(
            blob=data,
            format=self.mode,
            width=width,
            height=height
        )

        self.image = rgb

    @property
    def mode(self):
        if self.image.type in ALPHA_TYPES:
            return 'RGBA'

        return 'RGB'

    @property
    def size(self):
        return self.image.size

    def cleanup(self):
        Engine.exiftool.cleanup()
