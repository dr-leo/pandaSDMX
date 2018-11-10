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
from pathlib import Path
import sys
from tempfile import SpooledTemporaryFile
from warnings import warn

import requests


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

    def get(self, url=None, fromfile=None, params={}, headers={}):
        """Get SDMX message from REST service or local file.

        Args:
            url(str): URL of the REST service without the query part.
                If None (default), *fromfile* must be set.
            params(dict): will be appended as query part to the URL after a '?'
            fromfile(str): path to SDMX file containing an SDMX message.
                It will be passed on to the reader for parsing.
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
        if fromfile:
            # Load data from local file
            try:
                fromfile = Path(fromfile)
                # json files must be opened in text mode, all others in binary
                # as they may be zip files or xml.
                if fromfile.suffix == '.json':
                    mode_str = 'r'
                else:
                    mode_str = 'rb'
                source = open(fromfile, mode_str)
            except TypeError:
                # so fromfile must be file-like
                source = fromfile
            final_url = resp_headers = status_code = None
        else:
            source, final_url, resp_headers, status_code = self.request(
                url, params=params, headers=headers)
        return source, final_url, resp_headers, status_code

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
