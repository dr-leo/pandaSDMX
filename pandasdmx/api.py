# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this
# distribution.
# (c) 2014-2017 Dr. Leo <fhaxbox66qgmail.com>, all rights reserved


'''
This module defines two classes: :class:`pandasdmx.api.Request` and
:class:`pandasdmx.api.Response`. Together, these form the high-level API of
:mod:`pandasdmx`. Requesting data and metadata from an SDMX server requires a
good understanding of this API and a basic understanding of the SDMX web
service guidelines (only the chapters on REST services are relevant as
pandasdmx does not support the SOAP interface).

'''
from functools import partial, reduce
from importlib import import_module
from itertools import chain, product
import json
import logging
from operator import and_
from pathlib import Path
from pkg_resources import resource_string
import sys
from time import sleep
from zipfile import ZipFile, is_zipfile

import pandas as pd
from pandasdmx import remote
from pandasdmx.model import IdentifiableArtefact
import requests

logger = logging.getLogger(__name__)


if sys.version_info[0] == 3:
    str_type = str,
else:
    str_type = basestring,  # noqa: F821


class SDMXException(Exception):
    pass


class ResourceGetter(object):
    '''
    Descriptor to wrap Request.get vor convenient calls
    without specifying the resource as arg.
    '''

    def __init__(self, resource_type):
        self.resource_type = resource_type

    def __get__(self, inst, cls):
        return partial(inst.get, self.resource_type)


class Request(object):
    """Interface to an SDMX data provider.

    Parameters
    ----------
    agency (str): identifier of a data provider. Must be one of the dict keys
        in Request._agencies such as 'ESTAT', 'ECB', ''GSR' or ''. If '', the
        instance can only retrieve data or metadata from pre-fabricated URLs
        provided to :meth:`get`.
    log_level (int): override the package-wide logger with one of the
        :ref:`standard logging levels <py:levels>`. Default: None.
    session_opts: additional keyword arguments are passed to
        :class:`pandasdmx.remote.Session`.

    """
    # Load built-in agency metadata
    s = resource_string('pandasdmx', 'agencies.json').decode('utf8')
    _agencies = json.loads(s)
    del s

    @classmethod
    def load_agency_profile(cls, source):
        """Load metadata about a data provider.

        *source* must be a JSON-formated string or file-like object describing
        one or more data providers (URL of the SDMX web API, resource types,
        etc.).``Request._agencies`` is updated with the metadata from the
        source.

        Returns None
        """
        try:
            source = source.read()
        except AttributeError:
            pass
        new_agencies = json.loads(source)
        cls._agencies.update(new_agencies)

    @classmethod
    def list_agencies(cls):
        """eturn a sorted list of valid agency IDs.

        These can be used to create Request instances.
        """
        return sorted(list(cls._agencies))

    _resources = ['dataflow', 'datastructure', 'data', 'categoryscheme',
                  'codelist', 'conceptscheme']

    @classmethod
    def _make_get_wrappers(cls):
        for r in cls._resources:
            setattr(cls, r, ResourceGetter(r))

    def __init__(self, agency='', log_level=None, **session_opts):
        """Constructor."""
        # If needed, generate wrapper properties for get method
        if not hasattr(self, 'data'):
            self._make_get_wrappers()

        self.agency = agency.upper()

        self.session = remote.Session(**session_opts)

        if log_level:
            logging.getLogger('pandasdmx').setLevel(log_level)

    @property
    def agency(self):
        return self._agency

    @agency.setter
    def agency(self, value):
        if value in self._agencies:
            self._agency = value
        else:
            raise ValueError('If given, agency must be one of {0}'.format(
                list(self._agencies)))
        self.cache = {}  # for SDMX messages and other stuff.

    def clear_cache(self):
        self.cache.clear()

    @property
    def timeout(self):
        return self.session.timeout

    @timeout.setter
    def timeout(self, value):
        self.session.timeout = value

    def series_keys(self, flow_id, cache=True):
        """Get an empty dataset with all possible series keys.

        Return a pandas DataFrame. Each column represents a dimension, each row
        a series key of datasets of the given dataflow.
        """
        # download an empty dataset with all available series keys
        resp = self.data(flow_id, params={'detail': 'serieskeysonly'},
                         use_cache=True)
        print(resp.data[0].series)
        keys = list(s.key for s in resp.data[0].series.items())
        df = pd.DataFrame(keys, columns=keys[0]._fields, dtype='category')
        return df

    def _make_key(self, resource_type, resource_id, key):
        # If key is a dict, validate items against the DSD
        # and construct the key string which becomes part of the URL
        # Otherwise, do nothing as key must be a str confirming to the REST
        # API spec.
        if resource_type == 'data' and isinstance(key, dict):
            # select validation method based on agency capabilities
            if self._agencies[self.agency].get(
                    'supports_series_keys_only'):
                return self._make_key_from_series(resource_id, key)
            else:
                return self._make_key_from_dsd(resource_id, key)
        else:
            return None

    def _request_args(self, **kwargs):
        """Validate arguments and prepare pieces for a request."""
        parameters = kwargs.pop('params', {})
        headers = kwargs.pop('headers', {})

        # Base URL
        direct_url = kwargs.pop('url', None)
        if not direct_url:
            url_parts = [self._agencies[self.agency]['url']]
        else:
            url_parts = [direct_url]

        # Resource arguments
        resource = kwargs.pop('resource', None)
        resource_type = kwargs.pop('resource_type', None)
        resource_id = kwargs.pop('resource_id', None)
        if resource:
            assert isinstance(IdentifiableArtefact, resource)
            if resource_type:
                assert resource_type == resource.__class__.name
            else:
                resource_type = resource.__class__.name
            if resource_id:
                assert resource_id == resource.id, ValueError(
                    "mismatch between resource_id=%s and id '%s' of %r" %
                    (resource_id, resource.id, resource))
            else:
                resource_id = resource.id

        assert resource_type in self._resources, ValueError(
            'resource type %s not in must be one of %r' %
            (resource_type, self._resources))
        url_parts.append(resource_type)

        # Agency ID to use in the URL
        agency = kwargs.pop('agency', None)
        if resource_type in ['data', 'categoryscheme']:
            # Requests for these resources do not specific an agency in the URL
            agency_id = None
            assert agency is None, ValueError(
                "agency argument is redundant for resource type '%s'" %
                resource_type)
        else:
            agency_id = agency if agency else self.agency
        url_parts.extend([agency_id, resource_id])

        version = kwargs.pop('version', None)
        if not version and resource_type != 'data':
            url_parts.append('latest')

        url_parts.append(self._make_key(resource_type, resource_id,
                                        kwargs.pop('key', None)))

        # Assemble final URL
        url = '/'.join(filter(None, url_parts))

        # Parameters: set 'references' to sensible defaults
        if 'references' not in parameters:
            if resource_type in [
                    'dataflow', 'datastructure'] and resource_id:
                parameters['references'] = 'all'
            elif resource_type == 'categoryscheme':
                parameters['references'] = 'parentsandsiblings'

        # Headers: use headers from agency config if not given by the caller
        if not headers:
            headers = self._agencies[self.agency] \
                          .get('resources', {}) \
                          .get(resource_type, {}) \
                          .get('headers', {})

        assert len(kwargs) == 0, ValueError('unrecognized arguments: %r' %
                                            kwargs)

        return requests.Request('get', url, params=parameters,
                                headers=headers)

    def get(self, resource_type=None, resource_id=None, tofile=None,
            get_footer_url=(30, 3), use_cache=False, dry_run=False, **kwargs):
        """Get SDMX data or metadata and return it as a
        :class:`pandasdmx.Message` instance.

        get() can only construct URLs for the SDMX service set for this
        instance. Hence, you have to instantiate a
        :class:`pandasdmx.api.Request` instance for each data provider you want
        to access, or pass a pre-fabricated URL through the ``url`` parameter.

        Parameters
        ----------
        resource_type (str): the type of resource to be requested. Values must
            be one of the items in Request._resources such as 'data',
            'dataflow', 'categoryscheme' etc. It is used for URL construction,
            not to read the received SDMX file. Default: ''.
        resource_id (str): the id of the resource to be requested.
            It is used for URL construction. Defaults to ''.
        agency(str): ID of the agency providing the data or metadata.
            Used for URL construction only. It tells the SDMX web service
            which agency the requested information originates from. Note
            that an SDMX service may provide information from multiple data
            providers.
            Not to be confused with the agency ID passed to
            :meth:`__init__` which specifies the SDMX web service to be
            accessed.
        key(str, dict): select columns from a dataset by specifying
            dimension values.
            If type is str, it must conform to the SDMX REST API, i.e.
            dot-separated dimension values.
            If 'key' is of type 'dict', it must map dimension names to
            allowed dimension values. Two or more values can be separated
            by '+' as in the str form. The DSD will be downloaded and the
            items are validated against it before downloading the dataset.
        params(dict): defines the query part of the URL.
            The SDMX web service guidelines (www.sdmx.org) explain the
            meaning of permissible parameters. It can be used to restrict
            the time range of the data to be delivered (startperiod,
            endperiod), whether parents, siblings or descendants of the
            specified resource should be returned as well (e.g.
            references='parentsandsiblings'). Sensible defaults are set
            automatically depending on the values of other args such as
            `resource_type`.
            Defaults to {}.
        headers(dict): http headers. Given headers will overwrite
            instance-wide headers passed to the constructor. Defaults to
            None, i.e. use defaults from agency configuration.
        tofile (str or :py:`Path`): file path to write the received SDMX file
            on the fly. This is useful if you want to load data offline using
            `open_file()` or if you want to open an SDMX file in an XML editor.
        url (str): URL of the resource to download.
            If given, any other arguments such as ``resource_type`` or
            ``resource_id`` are ignored. Default is None.
        get_footer_url((int, int)):
            tuple of the form (seconds, number_of_attempts). Determines the
            behavior in case the received SDMX message has a footer where
            one of its lines is a valid URL. ``get_footer_url`` defines how
            many attempts should be made to request the resource at that
            URL after waiting so many seconds before each attempt.
            This behavior is useful when requesting large datasets from
            Eurostat. Other agencies do not seem to send such footers. Once
            an attempt to get the resource has been successful, the
            original message containing the footer is dismissed and the
            dataset is returned. The ``tofile`` argument is propagated.
            Note that the written file may be a zip archive. pandaSDMX
            handles zip archives since version 0.2.1. Defaults to (30, 3).
        memcache(str): If given, return Response instance if already in
            self.cache(dict), otherwise download resource and cache
            Response instance.

        Returns
        -------
        pandasdmx.api.Response: instance containing the requested
            SDMX Message.
        """
        req = self._request_args(resource_type=resource_type,
                                 resource_id=resource_id, **kwargs)
        req = self.session.prepare_request(req)

        # Now get the SDMX message via HTTP
        logger.info('Requesting resource from %s', req.url)
        logger.info('with headers %s' % req.headers)

        # Try to get resource from memory cache if specified
        if use_cache:
            try:
                return self.cache[req.url]
            except KeyError:
                logger.info('Not found in cache')
                pass

        if dry_run:
            return req

        response = self.session.send(req)

        # Select reader class
        if 'xml' in response.headers['content-type']:
            reader_module = import_module('pandasdmx.reader.sdmxml')
        elif 'json' in response.headers['content-type']:
            reader_module = import_module('pandasdmx.reader.sdmjson')
        else:
            raise ValueError("can't determine a reader for response content "
                             "type: %s" % response.headers['content-type'])

        # Instantiate reader
        reader = reader_module.Reader()

        # Maybe also copy the response to file as it's received
        arg = [tofile] if tofile else []

        # Parse the message
        msg = reader.read_message(remote.ResponseIO(response, *arg))

        # Store the HTTP response with the message
        msg.response = response

        # Disabled (refactoring)
        if False:
            # write msg to file and unzip it as required, then parse it
            if tofile:
                logger.info('Writing to file %s', tofile)
                with open(tofile, 'wb') as dest:
                    source.seek(0)
                    dest.write(source.read())
                    source.seek(0)
            # handle zip files
            if is_zipfile(source):
                temp = source
                with ZipFile(temp, mode='r') as zf:
                    info = zf.infolist()[0]
                    source = zf.open(info)
            else:
                # undo side effect of is_zipfile
                source.seek(0)

        # Check for URL in a footer and get the real data if so configured
        if get_footer_url and msg.footer is not None:
            logger.info('Footer found in SDMX message.')
            # Retrieve the first URL in the footer, if any
            url_l = [
                i for i in msg.footer.text if remote.is_url(i)]
            if url_l:
                # found an URL. Wait and try to request it
                footer_url = url_l[0]
                seconds, attempts = get_footer_url
                logger.info("Found URL in footer. Making %i requests, waiting "
                            " %i seconds in between.", attempts, seconds)
                for a in range(attempts):
                    sleep(seconds)
                    try:
                        return self.get(tofile=tofile, url=footer_url,
                                        headers=headers)
                    except Exception as e:
                        logger.info("Attempt #%i raised the following "
                                    " exception: %s", a, str(e))

        # store in memory cache if needed
        if use_cache:
            self.cache[req.url] = msg

        return msg

    def _make_key_from_dsd(self, flow_id, key):
        """Return a URL string for *key* in *flow_id*."""
        # Retrieve the DataflowDefinition
        df = self.get('dataflow', flow_id, use_cache=True).dataflow[flow_id]

        # Retrieve the DataStructureDefinition
        dsd_id = df.structure.id
        dsd = self.get('datastructure', dsd_id, use_cache=True) \
                  .structure[dsd_id]

        # Make a ContentConstraint from the key
        cc = dsd.make_cube(key)

        # TODO check that keys match dataflow constraints

        return cc.to_query_string(dsd)

    def _make_key_from_series(self, flow_id, key):
        '''
        Get all series keys by calling
        self.series_keys, and validate
        the key(dict) against it. Raises ValueError if
        a value does not occur in the respective
        set of dimension values. Multiple values per
        dimension can be provided as a list or in 'V1+V2' notation.

        Return: key(str)
        '''
        # get all series keys
        all_keys = self.series_keys(flow_id)
        dim_names = list(all_keys)
        # Validate the key dict
        # First, check correctness of dimension names
        invalid = [d for d in key
                   if d not in dim_names]
        if invalid:
            raise ValueError("Invalid dimension name {0}, allowed are: {1}"
                             .format(invalid, dim_names))
        # Pre-process key by expanding multiple values as list
        key = {k: v.split('+') if '+' in v else v for k, v in key.items()}
        # Check for each dimension name if values are correct and construct
        # string of the form 'value1.value2.value3+value4' etc.
        # First, wrap each single dim value in a list to allow
        # uniform treatment of single and multiple dim values.
        key_l = {k: [v] if isinstance(v, str_type) else v
                 for k, v in key.items()}
        # Iterate over the dimensions. If the key dict
        # contains an allowed value for the dimension,
        # it will become part of the string.
        invalid = list(chain.from_iterable((((k, v) for v in vl if v not in
                                             all_keys[k].values)
                                            for k, vl in key_l.items())))
        if invalid:
            raise ValueError("The following dimension values are invalid: {0}".
                             format(invalid))
        # Generate the 'Val1+Val2' notation for multiple dim values and remove
        # the lists
        for k, v in key_l.items():
            key_l[k] = '+'.join(v)
        # assemble the key string which goes into the URL
        parts = [key_l.get(name, '') for name in dim_names]
        return '.'.join(parts)

    def preview_data(self, flow_id, key=None, count=True, total=True):
        """
        Get keys or number of series for a prospective dataset query allowing
        for keys with multiple values per dimension.
        It downloads the complete list of series keys for a dataflow rather
        than using constraints and DSD. This feature is,
        however, not supported by all data providers.
        ECB and UNSD are known to work.

        Args:

        flow_id(str): dataflow id

        key(dict): optional key mapping dimension names to values or lists of
            values.
            Must have been validated before. It is not checked if key values
            are actually valid dimension names and values. Default: {}

        count(bool): if True (default), return the number of series
            of the dataset designated by flow_id and key. If False,
            the actual keys are returned as a pandas DataFrame or dict of
            dataframes, depending on the value of 'total'.

        total(bool): if True (default), return the aggregate number
            of series or a single dataframe (depending on the value of
            'count'). If False, return a dict mapping keys to dataframes of
            series keys. E.g., if key={'COUNTRY':'IT+CA+AU'}, the dict will
            have 3 items describing the series keys for each country
            respectively. If 'count' is True, dict values will be int rather
            than pd.DataFrame.
        """
        all_keys = self.series_keys(flow_id)
        # Handle the special case that no key is provided
        if not key:
            if count:
                return all_keys.shape[0]
            else:
                return all_keys

        # So there is a key specifying at least one dimension value.
        # Wrap single values in 1-elem list for uniform treatment
        key_l = {k: [v] if isinstance(v, str_type) else v
                 for k, v in key.items()}
        # order dim_names that are present in the key
        dim_names = [k for k in all_keys if k in key]
        # Drop columns that are not in the key
        key_df = all_keys.loc[:, dim_names]
        if total:
            # DataFrame with matching series keys
            bool_series = reduce(
                and_, (key_df.isin(key_l)[col] for col in dim_names))
            if count:
                return bool_series.value_counts()[True]
            else:
                return all_keys[bool_series]
        else:
            # Dict of value combinations as dict keys
            key_product = product(*(key_l[k] for k in dim_names))
            # Replace key tuples by namedtuples
            PartialKey = namedtuple_factory('PartialKey', dim_names)

            matches = {PartialKey(k): reduce(and_,
                       (key_df.isin({k1: [v1] for k1, v1 in zip(dim_names, k)}
                                    )[col] for col in dim_names))
                       for k in key_product}

            if not count:
                # dict mapping each key to DataFrame with selected key-set
                return {k: all_keys[v] for k, v in matches.items()}
            else:
                # Number of series per key
                return {k: v.value_counts()[True] for k, v in matches.items()}


def open_file(filename_or_obj):
    """Load a SDMX-ML or SDMX-JSON message from a file or file-like object.

    Parameters
    ----------
    filename_or_obj: str, Path, or file.
    """
    import pandasdmx.reader.sdmxml
    import pandasdmx.reader.sdmxjson

    readers = {
        'XML': pandasdmx.reader.sdmxml.Reader,
        'JSON': pandasdmx.reader.sdmxjson.Reader,
        }

    if isinstance(filename_or_obj, str):
        filename_or_obj = Path(filename_or_obj)

    try:
        # Use the file extension to guess the reader
        reader = readers[filename_or_obj.suffix.lstrip('.').upper()]

        # Open the file
        obj = open(filename_or_obj)
    except AttributeError:
        # File is already open
        pos = filename_or_obj.tell()
        first_line = filename_or_obj.readline().strip()
        filename_or_obj.seek(pos)

        if first_line.startswith('{'):
            reader = readers['JSON']
        elif first_line.startswith('<'):
            reader = readers['XML']
        else:
            raise ValueError(first_line)

    return reader().read_message(obj)


def to_pandas(obj, *args, **kwargs):
    """Convert an SDMX-IM *obj* to a pandas object."""
    from pandasdmx.writer import Writer

    return Writer().write(obj, *args, **kwargs)
