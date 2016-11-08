import fcntl
import logging
import os


class RotatingHandler(logging.handlers.RotatingFileHandler):
    '''This class rotates log files based on size, while supporting
    distinct python processes writing to the same file.

    Despite claims that lockf works on NFS shares, it didn't seem
    to be the case when testing on Vagrant. Therefore, don't store
    logs created with this class on a folder shared on NFS, otherwise
    the rollover won't be multiprocess-safe.
    '''

    def doRollover(self):
        lockName = "%s.lock" % self.baseFilename
        f = open(lockName, 'a+')

        try:
            fcntl.lockf(f.fileno(), fcntl.LOCK_EX)
        except IOError:
            # Couldn't acquire a lock, give up and rollover unsafely
            super(RotatingHandler, self).doRollover()
            f.close()
            return

        filesize = os.path.getsize(self.baseFilename)

        try:
            if filesize > self.maxBytes:
                # The reference file hasn't been rotated yet, let's do it
                super(RotatingHandler, self).doRollover()
            else:
                # We are probably still be looking at the old file, close the stream
                self.close()
                if not self.delay:
                    self.stream = self._open()
        finally:
            # Unlock no matter what
            fcntl.lockf(f.fileno(), fcntl.LOCK_UN)
            f.close()
