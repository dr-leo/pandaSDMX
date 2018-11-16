# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this
# distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>, all rights reserved

'''
This module is part of pandaSDMX. It contains
a classes for http access.
'''
from contextlib import closing
from io import BufferedIOBase
import logging
import sys
from tempfile import SpooledTemporaryFile
from warnings import warn

import requests
from requests.models import ITER_CHUNK_SIZE

try:
    from requests_cache import CachedSession as MaybeCachedSession
except ImportError:
    warn('optional dependency requests_cache is not installed; cache options '
         'to Session() have no effect', RuntimeWarning)
    from requests import Session as MaybeCachedSession

logger = logging.getLogger(__name__)


def is_url(s):
    '''
    return True if s (str) is a valid URL, False otherwise.
    '''
    return bool(requests.utils.urlparse(s).scheme)


class Session(MaybeCachedSession):
    """Simpler REST, built as a requests.Session subclass."""
    def __init__(self, **kwargs):
        # pandaSDMX-specific defaults
        stream = kwargs.pop('stream', True)
        proxies = kwargs.pop('proxies', None)
        self.timeout = kwargs.pop('timeout', 30.1)

        if MaybeCachedSession is not requests.Session:
            # Using requests_cache.CachedSession

            # No cache keyword arguments supplied = don't use the cache
            disabled = len(kwargs) == 0

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

    def get(self, url, **kwargs):
        response = super(Session, self).get(url, **kwargs)
        if response.status_code is requests.codes.not_implemented:
            raise NotImplementedError
        else:
            response.raise_for_status()
        return response


class ResponseIO(BufferedIOBase):
    """Pipe data from a requests.Response object.

    ResponseIO acts as a file-like object from which bytes can be read().
    Theses are received from the requests.Response object passed to the
    constructor as *response*.

    If *tee* is a filename, the contents of *response* are also written to this
    file as they are received.
    """

    def __init__(self, response, tee=None):
        self.response = response
        self.chunks = response.iter_content(ITER_CHUNK_SIZE)
        self.pending = bytes()
        self.tee = open(tee, 'wb') if tee else None

    def read(self, size=ITER_CHUNK_SIZE):
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
        return result
