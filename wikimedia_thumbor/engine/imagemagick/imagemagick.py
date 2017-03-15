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

from thumbor.utils import logger
from thumbor.engines import BaseEngine

from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.exiftool_runner import ExiftoolRunner


class ImageMagickException(Exception):
    pass


class Engine(BaseEngine):
    exiftool = ExiftoolRunner()

    def create_image(self, buffer):
        self.temp_file_created = False

        # This should be enough for now, if memory blows up on huge files we
        # can could use an mmap here
        if hasattr(self.context, 'wikimedia_original_file'):
            logger.debug('[IM] Grabbing filename from context')
            temp_file = self.context.wikimedia_original_file
        else:
            logger.debug('[IM] Dumping buffer into temp file')
            temp_file = NamedTemporaryFile(delete=False)
            temp_file.write(buffer)
            temp_file.close()
            self.temp_file_created = True

        self.exif = {}
        self.operators = []

        try:
            self.page = self.context.request.page - 1
        except AttributeError:
            self.page = 0

        # Read EXIF data from file first. This will get us the
        # size if we need it for the jpeg:size option, as well as the
        # ICC profile name in case we need to do profile swapping and
        # the various EXIF fields we want to keep
        self.read_exif(temp_file)

        return temp_file

    def jpeg_size(self):
        exif_image_size = self.exif['ImageSize']
        buffer_size = exif_image_size.split('x')
        buffer_size = [float(x) for x in buffer_size]
        buffer_ratio = buffer_size[0] / buffer_size[1]

        width = float(self.context.request.width)
        height = float(self.context.request.height)

        if width == 0:
            width = round(height * buffer_ratio, 0)

        if height == 0:
            height = round(width / buffer_ratio, 0)

        jpeg_size = '%dx%d' % (width, height)
        logger.debug('[IM] jpeg:size hint: %r' % jpeg_size)
        return jpeg_size

    def read_exif(self, input_temp_file):
        fields = [
            'ImageSize',
            'ProfileDescription',
            'ColorType'
        ]

        fields += self.context.config.EXIF_FIELDS_TO_KEEP

        command = [
            '-s',
            '-s',
        ]

        command += ['-{0}'.format(i) for i in fields]

        stdout = Engine.exiftool.command(
            pre=command,
            context=self.context,
            input_temp_file=input_temp_file
        )

        for s in stdout.splitlines():
            values = s.split(': ', 1)
            self.exif[values[0]] = values[1]

        logger.debug('[IM] EXIF: %r' % self.exif)

        if 'ImageSize' in self.exif:
            self.internal_size = map(int, self.exif['ImageSize'].split('x'))
        else:
            self.internal_size = (1, 1)

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

        self.icc_profile_saved = Engine.exiftool.command(
            pre=command,
            context=self.context,
            input_temp_file=input_temp_file
        )

    def process_exif(self, buffer):
        logger.debug('[IM] Processing EXIF')

        command = [
            '-m',
            '-all=',  # Strip all existing metadata
        ]

        # Create the temp file when we need it
        if hasattr(self, 'icc_profile_saved'):
            logger.debug('[IM] Putting saved ICC profile into temp file')
            profile_file = NamedTemporaryFile(delete=False)
            profile_file.write(self.icc_profile_saved)
            profile_file.close()
            self.icc_profile_path = profile_file.name
            del self.icc_profile_saved

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
            del self.icc_profile_path

        return stdout

    def read(self, extension=None, quality=None):
        logger.debug('[IM] read: %r %r' % (extension, quality))

        extension = extension.lstrip('.')

        config = self.context.config

        # -quality in ImageMagick has a different meaning for PNG
        # See https://www.imagemagick.org/script/command-line-options.php#quality
        if extension == 'png':
            quality = '95'

        operators = [
            '-quality',
            '%s' % quality
        ]

        if hasattr(config, 'CHROMA_SUBSAMPLING') and config.CHROMA_SUBSAMPLING:
            cs = config.CHROMA_SUBSAMPLING
            logger.debug('[IM] Chroma subsampling: %r' % cs)
            operators += [
                '-sampling-factor',
                cs
            ]

        logger.debug('[IM] Generating image with quality %r' % quality)

        if extension == 'jpg' and self.context.config.PROGRESSIVE_JPEG:
            operators += [
                '-interlace',
                'Plane'
            ]

        self.queue_operators(operators)

        last_operators = [
            '%s[%d]' % (self.image.name, self.page),
            '%s:-' % extension,
        ]

        returncode, stderr, result = self.run_operators(last_operators)

        # If the requested page failed, try the cover
        if returncode != 0 and self.page > 0:
            self.page = 0
            last_operators = [
                '%s[%d]' % (self.image.name, self.page),
                '%s:-' % extension,
            ]
            returncode, stderr, result = self.run_operators(last_operators)

        if returncode != 0:
            if self.temp_file_created:
                ShellRunner.rm_f(self.image.name)
                self.temp_file_created = False
            raise ImageMagickException('Failed to convert image: %s' % stderr)

        self.operators = []

        # Going forward, we're dealing with a single page document
        if self.page > 0:
            self.page = 0

        if extension == 'jpg':
            result = self.process_exif(result)

        if self.temp_file_created:
            ShellRunner.rm_f(self.image.name)
            self.temp_file_created = False

        return result

    def crop(self, crop_left, crop_top, crop_right, crop_bottom):
        logger.debug(
            '[IM] crop: %r %r %r %r' % (
                crop_left,
                crop_top,
                crop_right,
                crop_bottom
            )
        )

        # Sometimes thumbor's resize algorithm will try to pre-crop
        # the image. However that gets in the way of the jpeg:size
        # optimization. I presume Thumbor does that to reduce interpolation
        # but it does so at the expense of cutting off one edge of the image
        if not hasattr(self, 'buffer'):
            width = int(crop_right) - int(crop_left)
            height = int(crop_bottom) - int(crop_top)

            operators = [
                '-crop',
                '%dx%d+%d+%d' % (width, height, crop_left, crop_top)
            ]

            self.queue_operators(operators)

    def resize(self, width, height):
        logger.debug('[IM] resize: %r %r' % (width, height))

        self.internal_size = (width, height)

        operators = []

        if self.extension == '.jpg':
            operators += [
                '-define',
                'jpeg:size=%s' % self.jpeg_size()
            ]

        operators += [
            '-resize',
            '%dx%d' % (int(width), int(height))
        ]

        self.queue_operators(operators)

    def flip_horizontally(self):
        logger.debug('[IM] flip_horizontally')

        self.queue_operators(['-flop'])

    def flip_vertically(self):
        logger.debug('[IM] flip_vertically')

        self.queue_operators(['-flip'])

    def rotate(self, degrees):
        logger.debug('[IM] rotate: %r' % degrees)

        self.queue_operators(['-rotate', '%s' % degrees])

    def reorientate(self):
        logger.debug('[IM] reorientate')

        self.queue_operators(['-auto-orient'])

    def image_data_as_rgb(self, update_image=True):
        logger.debug('[IM] image_data_as_rgb: %r' % update_image)

        operators = [
            '%s[%d]' % (self.image.name, self.page),
            '%s:-' % self.mode
        ]

        returncode, stderr, converted = self.run_operators(operators)

        # If the requested page failed, try the cover
        if returncode != 0 and self.page > 0:
            self.page = 0
            operators = [
                '%s[%d]' % (self.image.name, self.page),
                '%s:-' % self.mode
            ]
            returncode, stderr, converted = self.run_operators(operators)

        if returncode != 0:
            if self.temp_file_created:
                ShellRunner.rm_f(self.image.name)
                self.temp_file_created = False
            raise ImageMagickException('Failed to convert image to %s: %s' % (self.mode, stderr))

        self.operators = []

        # Going forward, we're dealing with a single page document
        if self.page > 0:
            self.page = 0

        if update_image:
            with open(self.image.name, 'w') as f:
                f.write(converted)

        return self.mode, converted

    def set_image_data(self, data):
        logger.debug('[IM] set_image_data')

        with open(self.image.name, 'w') as f:
            f.write(data)

    @property
    def mode(self):
        if 'ColorType' in self.exif and self.exif['ColorType'] == 'RGB with Alpha':
            return 'RGBA'

        return 'RGB'

    @property
    def size(self):
        return self.internal_size

    def queue_operators(self, operators):
        self.operators += operators

        logger.debug('[IM] Queued operators: %r' % self.operators)

    def run_operators(self, extra_operators):
        command = [
            self.context.config.CONVERT_PATH,
            '-define',
            'tiff:exif-properties=no'  # Otherwise IM treats a bunch of warnings as errors
        ]

        command += self.operators

        command += extra_operators

        returncode, stderr, stdout = ShellRunner.command(
            command,
            self.context,
        )

        return returncode, stderr, stdout
