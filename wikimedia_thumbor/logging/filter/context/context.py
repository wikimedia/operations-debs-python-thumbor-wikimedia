import logging


class ContextFilter(logging.Filter):
    '''This class grabs the port Thumbor is running on from the first debug
    message emitted by Thumbor and adds it to the LogRecord of every subsequent
    log message.

    This is needed to identify which thumbor instance is which in the logs,
    because we typically run Thumbor inside firejail. Firejail hides the parent
    pid from the process, making logging by pid in python impossible. All
    thumbor processes have pid 2 from their own perspective. While logging
    by port isn't ideal, it's better than not being able to tell Thumbor
    processes apart at all.

    If ports are insufficient in the long run, we might want to add a unique id
    to the context as well and this class would be the right place to do it.
    '''
    port = '????'  # For some very early log messages before the port is open

    def __init__(self, flag=None):
        self.flag = flag

    def filter(self, record):
        import re
        # Look for the port if we haven't found it yet
        if type(self).port == '????':
            matches = re.match(
                '.*thumbor running at \d+.\d+.\d+.\d+:([\d]+).*',
                record.msg
            )

        if matches:
            # It's a match, save the port and use it from this point on
            type(self).port = matches.group(1)

        record.port = type(self).port

        # Only let the log message through if we are told to through the flag
        return self.flag == 'log'
