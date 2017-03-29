import logging


class ThumborFormatter(logging.Formatter):
    '''This class handlers custom log formatting, to
    allow for optional extras.
    '''

    def format(self, record):
        if not hasattr(record, 'url'):
            record.url = ''

        return super(ThumborFormatter, self).format(record)
