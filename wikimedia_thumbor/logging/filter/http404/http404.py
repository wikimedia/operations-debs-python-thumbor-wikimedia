import logging


class Http404Filter(logging.Filter):
    '''This class filters 404 warning messages. It can either exclude such
    messages from the logs or only let those messages through. Which allows us
    to direct those specific messages to a separate file while removing those
    log entries from the main log file.'''
    def __init__(self, flag=None):
        self.flag = flag

    def filter(self, record):
        import re
        matches = re.match('.*HTTP 404.*', record.msg)

        if self.flag == 'exclude':
            return not matches
        elif self.flag == 'only':
            return matches

        return True