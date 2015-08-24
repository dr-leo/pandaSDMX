# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>, all rights reserved

'''
This module is part of pandaSDMX. It contains
a classes for http access.
'''


import requests
from tempfile import SpooledTemporaryFile as STF
from contextlib import closing
try:
    import requests_cache
except ImportError:
    pass


class REST:

    """
    Query SDMX resources via REST or from a file

    The constructor accepts arbitrary keyword arguments that will be passed
    to the requests.get function on each call. This makes the REST class somewhat similar to a requests.Session. E.g., proxies or
    authorisation data needs only be provided once. The keyword arguments are
    stored in self.config. Modify this dict to issue the next 'get' request with
    changed arguments.
    """

    max_size = 2 ** 24
    '''upper bound for in-memory temp file. Larger files will be spooled from disc'''

    def __init__(self, cache, http_cfg):
        default_cfg = dict(stream=True, timeout=30.1)
        for it in default_cfg.items():
            http_cfg.setdefault(*it)
        self.config = http_cfg
        if cache:
            requests_cache.install_cache(**cache)

    def get(self, url, fromfile=None, params={}):
        '''Get SDMX message from REST service or local file

        Args:

            url(str): URL of the REST service without the query part
                If None, fromfile must be set. Default is None
            params(dict): will be appended as query part to the URL after a '?'
            fromfile(str): path to SDMX file containing an SDMX message.
                It will be passed on to the
                reader for parsing.

        Returns:
            tuple: three objects:

                0. file-like object containing the SDMX message
                1. the complete URL, if any, including the query part
                   constructed from params
                2. the status code

        Raises:
            HTTPError if SDMX service responded with
                status code 401. Otherwise, the status code
                is returned
 '''
        if fromfile:
            try:
                # Load data from local file
                source = open(fromfile, 'rb')
            except TypeError:
                # so fromfile must be file-like
                source = fromfile
            final_url = headers = status_code = None
        else:
            source, final_url, headers, status_code = self.request(
                url, params=params)
        return source, final_url, headers, status_code

    def request(self, url, params={}):
        """
        Retrieve SDMX messages.
        If needed, override in subclasses to support other data providers.

        :param url: The URL of the message.
        :type url: str
        :return: the xml data as file-like object
        """

        with closing(requests.get(url, params=params, **self.config)) as response:
            if response.status_code == requests.codes.OK:
                source = STF(max_size=self.max_size)
                for c in response.iter_content(chunk_size=1000000):
                    source.write(c)

            else:
                source = None
            code = int(response.status_code)
            if 400 <= code <= 499:
                raise response.raise_for_status()
            return source, response.url, response.headers, code
