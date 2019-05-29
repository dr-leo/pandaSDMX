from io import BufferedIOBase
import logging
from warnings import warn

import requests
from requests.models import ITER_CHUNK_SIZE

try:
    from requests_cache import CachedSession as MaybeCachedSession
except ImportError:  # pragma: no cover
    warn('optional dependency requests_cache is not installed; cache options '
         'to Session() have no effect', RuntimeWarning)
    from requests import Session as MaybeCachedSession


logger = logging.getLogger(__name__)


class Session(MaybeCachedSession):
    """:class:`requests.Session` subclass with optional caching.

    If requests_cache is installed, this class caches responses.
    """
    def __init__(self, **kwargs):
        # pandaSDMX-specific defaults
        stream = kwargs.pop('stream', True)
        proxies = kwargs.pop('proxies', None)
        self.timeout = kwargs.pop('timeout', 30.1)

        if MaybeCachedSession is not requests.Session:
            # Using requests_cache.CachedSession

            # No cache keyword arguments supplied = don't use the cache
            disabled = set(kwargs.keys()) <= {'get_footer_url'}

            if disabled:
                # Avoid creating any file
                kwargs['backend'] = 'memory'

            super(Session, self).__init__(**kwargs)

            # Overwrite value from requests_cache.CachedSession.__init__()
            self._is_cache_disabled = disabled
        elif len(kwargs):
            raise ValueError('Cache arguments have no effect without '
                             'requests_session: %s' % kwargs)
        else:
            # Plain requests.Session
            super(Session, self).__init__()

        # Overwrite values from requests.Session.__init__()
        self.stream = stream
        self.proxies = proxies


class ResponseIO(BufferedIOBase):
    """Pipe data from a :class:`requests.Response` object, with echo to file.

    :class:`ResponseIO` wraps a :class:`requests.Response` object's 'content'
    attribute, providing a file-like object from which bytes can be
    :meth:`read` incrementally.

    Parameters
    ----------
    response : :class:`requests.Response`
        HTTP response to wrap.
    tee : :py:class:`os.PathLike`, optional
        If provided, the contents of the response are also written to this file
        as they are received. The file is closed automatically when *response*
        reaches EOF.
    """

    def __init__(self, response, tee=None):
        self.response = response
        self.chunks = response.iter_content(ITER_CHUNK_SIZE)
        self.pending = bytes()
        self.tee_filename = tee
        # str() here is for Python 3.5 compatibility
        self.tee = open(str(tee), 'wb') if tee else None

    def read(self, size=ITER_CHUNK_SIZE):
        """Read and return up to *size* bytes.

        If the argument is omitted, :py:obj:`None`, or negative, reads and
        returns all data until EOF. If *tee* was provided to the constructor,
        data is echoed to file.

        If the argument is positive, and the underlying raw stream is not
        ‘interactive’, multiple raw reads may be issued to satisfy the byte
        count (unless EOF is reached first).

        Returns an empty bytes object on EOF.

        """
        try:
            # Accumulate chunks until the requested size is reached
            while len(self.pending) < size:
                self.pending += next(self.chunks)

            # Return the requested amount
            result = self.pending[:size]
            self.pending = self.pending[size:]
        except StopIteration:
            # Out of chunks; return the remaining content
            result = self.pending
            # Will trigger TypeError on next read()
            self.pending = None
        except TypeError:
            # Last call to read() must return empty bytes()
            result = bytes()

        if self.tee:
            self.tee.write(result)
            if len(result) == 0:
                # Also close the results file
                self.tee.close()

        return result
