import logging


class ErrorFilter(logging.Filter):
    '''This class filters out redundant logger.error messages coming from Thumbor
    '''
    def filter(self, record):
        if (record.msg.startswith('ERROR: Traceback')
                or record.msg.startswith('[BaseHandler] get_image failed for url')):
            return False

        return True
