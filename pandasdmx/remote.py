import logging
import os
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

    def __init__(
        self,
        timeout=30.1,
        proxies=None,
        stream=False,
        auth=None,
        cert=None,
        verify=True,
        **kwargs,
    ):

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
        # TODO: consider passing these values to __init__, but manage
        # the ugly 'get_footer' stuff
        self.proxies = proxies
        self.timeout = timeout
        self.stream = stream
        self.auth = auth
        self.cert = cert
        self.verify = verify


class ResponseIO(BufferedIOBase):
    """Buffered wrapper for :class:`requests.Response` with optional file output.

    :class:`ResponseIO` wraps a :class:`requests.Response` object's 'content'
    attribute, providing a file-like object from which bytes can be :meth:`read`
    incrementally.

    Parameters
    ----------
    response : :class:`requests.Response`
        HTTP response to wrap.
    tee : binary, writable :py:class:`io.BufferedIOBase`, or :class:`fsspec.core.OpenFile` 
        or :class:`io.PathLike`, defaults to io.BytesIO.
        If *tee* is an open binary file, it is used to store the received data.
        If *tee* is a PathLike, it is passed to  :func:`open`, .  
        *tee* is exposed as *self.tee* and not closed, so this class may be instantiated
        in a with-context. The latter is also 
        recommended if a :class:`fsspec.core.OpenFile` is passed.
    """

    def __init__(self, response, tee=None):
        self.response = response
        # Open a new file in various scenarios, or assume that tee is an open file
        if tee is None:
            tee = BytesIO()
        elif isinstance(tee, (str, os.PathLike)):
            tee = open(tee, mode="w+b")
        # Handle the special case of a fsspec.OpenFile
        if isinstance(tee, list):
            assert len(tee) == 1, ValueError(f"Only 1 file allowed, {len(tee)} given.")
            tee = tee[0]
        # Now tee must be an open file, including when passed as such
        #   use tee as instance cache
        self.tee = tee

        # write content, but do not close the file.
        tee.write(response.content)
        tee.flush()
        tee.seek(0)

    def readable(self):
        return True

    def read(self, size=-1):
        """Read and return up to `size` bytes by calling ``self.tee.read()``."""
        return self.tee.read(size)

    def close(self):
        self.tee.close()
