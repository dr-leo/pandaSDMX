try:
    import fsspec
    # use fsspec for file-handling if available
    open_ = fsspec.open_files
except ImportError:
    # fall back to  stdlib open if fsspec is unavailable
    open_ = open

import logging
from io import BufferedIOBase, BytesIO
from warnings import warn

import requests

try:
    from requests_cache import CachedSession as MaybeCachedSession
except ImportError:  # pragma: no cover
    warn(
        "optional dependency requests_cache is not installed; cache options "
        "to Session() have no effect",
        RuntimeWarning,
    )
    from requests import Session as MaybeCachedSession


logger = logging.getLogger(__name__)


class Session(MaybeCachedSession):
    """:class:`requests.Session` subclass with optional caching.

    If requests_cache is installed, this class caches responses.
    """

    def __init__(self, timeout=30.1, proxies=None, stream=False, **kwargs):

        if MaybeCachedSession is not requests.Session:
            # Using requests_cache.CachedSession

            # No cache keyword arguments supplied = don't use the cache
            disabled = set(kwargs.keys()) <= {"get_footer_url"}

            if disabled:
                # Avoid creating any file
                kwargs["backend"] = "memory"

            super(Session, self).__init__(**kwargs)

            # Overwrite value from requests_cache.CachedSession.__init__()
            self._is_cache_disabled = disabled
        elif len(kwargs):
            raise ValueError(
                "Cache arguments have no effect without "
                "requests_session: %s" % kwargs
            )
        else:
            # Plain requests.Session
            super(Session, self).__init__()

        # Overwrite values from requests.Session.__init__()
        self.proxies = proxies
        self.timeout = timeout
        self.stream = stream


class ResponseIO(BufferedIOBase):
    """Buffered wrapper for :class:`requests.Response` with optional file output.

    :class:`ResponseIO` wraps a :class:`requests.Response` object's 'content'
    attribute, providing a file-like object from which bytes can be :meth:`read`
    incrementally.

    Parameters
    ----------
    response : :class:`requests.Response`
        HTTP response to wrap.
    tee : binary, writable :py:class:`io.BufferedIOBasè`, defaults to io.BytesIO()
        *tee* is exposed as *self.tee* and not closed explicitly.
    """

    def __init__(self, response, tee=None):
        self.response = response
        if tee is None:
            tee = BytesIO()
        # If tee is a file-like object, then use it as cache
        if (isinstance(tee, BufferedIOBase) # normal file 
            or 'tempfile' in str(tee) # tempfile 
            or 'fsspec' in str(tee.__class__)): # fsspec.core.Openfiles
            self.tee = tee
        elif isinstance(tee, dict):
            tee.setdefault('mode', default='w+b')
            self.tee = open_(**tee)
            #  self.tee may be an open stdlib file or a fsspec not yet opened one
        else:
            # So tee must be str or PathLike
            self.tee = open_(tee, mode="w+b")
        # if tee is a temp file, write content, but do not close it.
        if hasattr(self.tee, "file"):
            self.tee.write(response.content)
            self.tee.flush()
            self.tee.seek(0)
        else:
            # In all other cases: write content and close the file
            with self.tee as f:
                # If tee is an fsspec.OpenFile, f is a list. Take its first item.
                f_ = f[0] if isinstance(f, list) else f
                f_.write(response.content)

    def readable(self):
        return True

    def read(self, size=-1):
        """Read and return up to `size` bytes by calling ``self.tee.read()``."""
        return self.tee.read(size)
