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
from http import HTTPStatus
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


def STF(*args, **kwargs):
    """Create a SpooledTemporaryFile, ensuring Python 2 compatibility."""
    if sys.version_info[0] < 3:
        kwargs.pop('encoding', None)
    return SpooledTemporaryFile(*args, **kwargs)


def install_cache(**kwargs):
    """Install cache, or raise a warning."""
    try:
        import requests_cache
        requests_cache.install_cache(**kwargs)
    except ImportError:
        warn('optional dependency requests_cache is not installed; options '
             'REST(…, cache=%r, …) have no effect' % kwargs, RuntimeWarning)


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
        if response.status_code == HTTPStatus.NOT_IMPLEMENTED:
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


class REST:
    """Query SDMX resources via REST or from a file.

    The constructor accepts arbitrary keyword arguments that will be passed
    to the requests.get function on each call. This makes the REST class
    somewhat similar to a requests.Session. E.g., proxies or authorisation data
    needs only be provided once. The keyword arguments are stored in
    self.config. Modify this dict to issue the next 'get' request with
    changed arguments.
    """

    # Upper bound for in-memory temp file. Larger files will be spooled from
    # disk
    max_size = 2 ** 24

    def __init__(self, cache=None, http_cfg={}):
        default_cfg = dict(stream=True, timeout=30.1)
        default_cfg.update(http_cfg)
        self.config = default_cfg

        if cache:
            install_cache(**cache)

    def get(self, url=None, params={}, headers={}):
        """Get SDMX message from REST service or local file.

        Args:
            url(str): URL of the REST service without the query part.
                If None (default), *fromfile* must be set.
            params(dict): will be appended as query part to the URL after a '?'
            headers(dict): http headers. Overwrite instance-wide headers.
                Default is {}.

        Returns:
            tuple: three objects:

                0. file-like object containing the SDMX message
                1. the complete URL, if any, including the query part
                   constructed from params
                2. the status code

        Raises:
            HTTPError if SDMX service responded with status code 401.
            Otherwise, the status code is returned.
        """
        return self.request(url, params=params, headers=headers)

    def request(self, url, params={}, headers={}):
        """
        Retrieve SDMX messages.
        If needed, override in subclasses to support other data providers.

        :param url: The URL of the message.
        :type url: str
        :return: the xml data as file-like object
        """
        # Generate current config. Merge in any given headers
        cur_config = self.config.copy()
        if 'headers' in cur_config:
            cur_config['headers'] = cur_config['headers'].copy()
            cur_config['headers'].update(headers)
        else:
            cur_config['headers'] = headers

        with closing(requests.get(url, params=params, **cur_config)) as \
                response:
            if response.status_code == requests.codes.OK:
                # Prepare the temp file. xml content will be
                # stored in a binary file, json in a textfile.
                if (response.headers.get('Content-Type')
                        and ('json' in response.headers['Content-Type'])):
                    enc, fmode = response.encoding, 'w+t'
                else:
                    enc, fmode = None, 'w+b'
                # Create temporary file
                source = STF(max_size=self.max_size, mode=fmode, encoding=enc)
                for c in response.iter_content(chunk_size=1000000,
                                               decode_unicode=bool(enc)):
                    source.write(c)

            else:
                source = None
            code = int(response.status_code)
            if 400 <= code <= 499:
                raise response.raise_for_status()
            return source, response.url, response.headers, code
