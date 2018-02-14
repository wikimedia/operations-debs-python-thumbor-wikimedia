#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback

from thumbor.utils import logger
from wikimedia_thumbor.logging import log_extra


class ErrorHandler(object):
    def __init__(self, config, client=None):
        pass

    def handle_error(self, context, handler, exception):
        ex_type, value, tb = exception

        ex_msg = traceback.format_exception_only(ex_type, value)
        tb_msg = traceback.format_tb(tb)

        extra = log_extra(context)
        extra['traceback'] = ''.join(tb_msg)

        logger.error(''.join(ex_msg), extra=extra)
