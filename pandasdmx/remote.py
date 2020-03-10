from io import BufferedIOBase, BytesIO
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

    #: Timeout interval in seconds for queries.
    timeout = 30

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
    """Read  data from a :class:`requests.Response` object, into an in-memory or on-disk file 
    and expose it as a file-like object.

    :class:`ResponseIO` wraps a :class:`requests.Response` object's 'content'
    attribute, providing a file-like object from which bytes can be
    :meth:`read` incrementally.

    Parameters
    ----------
    response : :class:`requests.Response`
        HTTP response to wrap.
    tee : binary, writable :py:class:`io.BufferedIOBasè`, defaults to io.BytesIO()
        *tee* is exposed as *self.tee* and not closed explicitly.
    """

    def __init__(self, response, tee=None):
        self.response = response
        self.tee = tee or BytesIO()
        self.tee.write(response.content)
        self.tee.seek(0)

    def readable(self):
        return True

    def read(self, size=-1):
        """Read and return up to *size* bytes by calling *tee.write()*.

        Defaults to -1. In this case,   reads and
        returns all data until EOF. 

        Returns an empty bytes object on EOF.
        """
        return self.tee.read(size)
