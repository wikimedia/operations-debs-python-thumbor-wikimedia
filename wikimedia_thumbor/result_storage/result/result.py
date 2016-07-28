#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 Wikimedia Foundation

import hashlib
import shutil
import urllib
from os.path import exists, join

from thumbor.result_storages.file_storage import Storage as BaseFileStorage


class Storage(BaseFileStorage):
    def normalize_path(self, path):
        root_path = self.context.config.RESULT_STORAGE_FILE_STORAGE_ROOT_PATH
        rstripped_root_path = root_path.rstrip('/')
        path_segments = [
            rstripped_root_path,
            Storage.PATH_FORMAT_VERSION,
        ]

        if self.is_auto_webp:
            path_segments.append('webp')

        decoded_path = urllib.unquote(path)

        # Hack, but thumbor passes the full path to this function
        # which doesn't let us distinguish parameters from
        # source URL
        decoded_image_url = urllib.unquote(self.context.request.image_url)

        cleared_path = decoded_path.replace(decoded_image_url, '')
        decoded_parameters = cleared_path.rstrip('/')

        url_segments = [
            hashlib.sha1(decoded_image_url).hexdigest(),
            hashlib.sha1(decoded_parameters).hexdigest()
        ]

        reversed_url = '/'.join(url_segments)

        path_segments.extend([self.partition(reversed_url), reversed_url, ])

        normalized_path = join(*path_segments)

        return normalized_path

    def remove(self, path):
        decoded_path = urllib.unquote(path)
        root_path = self.context.config.RESULT_STORAGE_FILE_STORAGE_ROOT_PATH
        rstripped_root_path = root_path.rstrip('/')

        path_segments = [
            rstripped_root_path,
            Storage.PATH_FORMAT_VERSION,
        ]

        if self.is_auto_webp:
            path_segments.append('webp')

        hashed_url = hashlib.sha1(decoded_path.replace('http://', ''))
        digested_url = hashed_url.hexdigest()
        path_segments.extend([self.partition(digested_url), digested_url, ])

        normalized_path = join(*path_segments)

        if exists(normalized_path):
            shutil.rmtree(normalized_path)
