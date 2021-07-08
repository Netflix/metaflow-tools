import os
import shutil
import tempfile
import time

HOUR = 60 * 60

def refresh_timestamp(f):
    def wrapper(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        finally:
            self._refresh_timestamp()
    return wrapper

def garbage_collect(f):
    def wrapper(self, *args, **kwargs):
        self._garbage_collect()
        return f(self, *args, **kwargs)
    return wrapper

class ExpiringDirectory(object):

    def __init__(self, top, root, ttl):
        self._makedirs(top)
        self.top = top
        self.root = os.path.join(top, root)
        self.ttl = ttl
        if self.is_cached:
            self._refresh_timestamp()

    def _refresh_timestamp(self):
        with tempfile.NamedTemporaryFile(dir=self.root,
                                         mode='w',
                                         prefix='.last_',
                                         delete=False) as f:
            f.write(str(time.time()))
            f.flush()
            os.rename(f.name, os.path.join(self.root, '.last'))

    @property
    def is_cached(self):
        # we must not use soon-to-expire directories, see
        # comments in _garbage_collect() below. Hence the
        # " - HOUR" check below.
        return os.path.exists(self.root) and\
               not self._should_be_deleted(self.root, self.ttl - HOUR)

    def _should_be_deleted(self, root, ttl):
        last_access = os.path.join(root, '.last')
        tstamp = None
        if os.path.exists(last_access):
            try:
                with open(last_access) as f:
                    tstamp = float(f.read())
            except:
                pass
        if tstamp is None:
            try:
                tstamp = os.stat(root).st_ctime
            except:
                pass
        if tstamp is not None:
            return time.time() - tstamp > ttl
        return False

    def _garbage_collect(self):
        for subdir in os.listdir(self.top):
            root = os.path.join(self.top, subdir)
            if os.path.islink(root):
                continue
            if self._should_be_deleted(root, self.ttl):
                try:
                    # it is important that we delete the symlink
                    # first before the directory itself, if the
                    # symlink points to this directory.
                    maybe_link = '.'.join(root.split('.')[:-1])
                    if os.path.exists(maybe_link) and\
                       os.path.samefile(maybe_link, root):
                        # there's a race condition between
                        # samefile() and unlink(), if a concurrent
                        # _download_and_extract() updates the link
                        # between the two operations. Hence it is
                        # important that we don't use directories
                        # that are about to expire soon. We take
                        # care of this in __init__().
                        os.unlink(maybe_link)
                    shutil.rmtree(root)
                except:
                    pass

    def _makedirs(self, path):
        try:
            os.makedirs(path)
        except OSError as x:
            if x.errno == 17:
                return
            else:
                raise
