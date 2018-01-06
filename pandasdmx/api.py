# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this distribution.
# (c) 2014-2017 Dr. Leo <fhaxbox66qgmail.com>, all rights reserved


'''
This module defines two classes: :class:`pandasdmx.api.Request` and :class:`pandasdmx.api.Response`.
Together, these form the high-level API of :mod:`pandasdmx`. Requesting data and metadata from
an SDMX server requires a good understanding of this API and a basic understanding of the SDMX web service guidelines
only the chapters on REST services are relevant as pandasdmx does not support the
SOAP interface.

'''

from pandasdmx import remote
from pandasdmx.utils import str_type, namedtuple_factory
import pandas as PD
from pkg_resources import resource_string
from importlib import import_module
from zipfile import ZipFile, is_zipfile
from time import sleep
from functools import partial, reduce
from itertools import chain, product
from operator import and_
import logging
import json


logger = logging.getLogger('pandasdmx.api')


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

    """Get SDMX data and metadata from remote servers or local files.
    """
    # Load built-in agency metadata
    s = resource_string('pandasdmx', 'agencies.json').decode('utf8')
    _agencies = json.loads(s)
    del s

    @classmethod
    def load_agency_profile(cls, source):
        '''
        Classmethod loading metadata on a data provider. ``source`` must
        be a json-formated string or file-like object describing one or more data providers
        (URL of the SDMX web API, resource types etc.
        The dict ``Request._agencies`` is updated with the metadata from the
        source.

        Returns None
        '''
        if not isinstance(source, str_type):
            # so it must be a text file
            source = source.read()
        new_agencies = json.loads(source)
        cls._agencies.update(new_agencies)

    @classmethod
    def list_agencies(cls):
        '''
        Return a sorted list of valid agency IDs. These can be used to create ``Request`` instances.  
        '''
        return sorted(list(cls._agencies))

    _resources = ['dataflow', 'datastructure', 'data', 'categoryscheme',
                  'codelist', 'conceptscheme']

    @classmethod
    def _make_get_wrappers(cls):
        for r in cls._resources:
            setattr(cls, r, ResourceGetter(r))

    def __init__(self, agency='', cache=None, log_level=None,
                 **http_cfg):
        '''
        Set the SDMX agency, and configure http requests for this instance.

        Args:

            agency(str): identifier of a data provider.
                Must be one of the dict keys in Request._agencies such as
                'ESTAT', 'ECB', ''GSR' or ''.
                An empty string has the effect that the instance can only
                load data or metadata from files or a pre-fabricated URL. .
                defaults to '', i.e. no agency.

            cache(dict): args to be passed on to 
                ``requests_cache.install_cache()``. Default is None (no caching).
            log_level(int): set log level for lib-wide logger as set up in pandasdmx.__init__.py. 
                For details see the docs on the 
                logging package from the standard lib. Default: None (= do nothing).
            **http_cfg: used to configure http requests. E.g., you can 
            specify proxies, authentication information and more.
            See also the docs of the ``requests`` package at 
            http://www.python-requests.org/en/latest/.   
        '''
        # If needed, generate wrapper properties for get method
        if not hasattr(self, 'data'):
            self._make_get_wrappers()
        self.client = remote.REST(cache, http_cfg)
        self.agency = agency.upper()
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

    def clear_cache(self, key=None):
        '''
        If key is Non (default), remove the item if it exists. 
        Otherwise, clear the entire cache.
        '''
        if key:
            if key in self.cache:
                del self.cache[key]
        else:
            self.cache.clear()

    @property
    def timeout(self):
        return self.client.config['timeout']

    @timeout.setter
    def timeout(self, value):
        self.client.config['timeout'] = value

    def series_keys(self, flow_id, cache=True, dsd=None):
        '''
        Get an empty dataset with all possible series keys.

        Return a pandas DataFrame. Each
        column represents a dimension, each row
        a series key of datasets of 
        the given dataflow.
        '''
        # Check if requested series keys are already cached
        cache_id = 'series_keys_' + flow_id
        if cache_id in self.cache:
            return self.cache[cache_id]
        else:
            # download an empty dataset with all available series keys
            resp = self.data(flow_id, params={'detail': 'serieskeysonly'},
                             dsd=dsd)
            l = list(s.key for s in resp.data.series)
            df = PD.DataFrame(l, columns=l[0]._fields, dtype='category')
            if cache:
                self.cache[cache_id] = df
            return df

    def get(self, resource_type='', resource_id='', agency='',
            version=None, key='',
            params={}, headers={},
            fromfile=None, tofile=None, url=None, get_footer_url=(30, 3),
            memcache=None, writer=None, dsd=None):
        '''get SDMX data or metadata and return it as a :class:`pandasdmx.api.Response` instance.

        While 'get' can load any SDMX file (also as zip-file) specified by 'fromfile',
        it can only construct URLs for the SDMX service set for this instance.
        Hence, you have to instantiate a :class:`pandasdmx.api.Request` instance for each data provider you want to access, or
        pass a pre-fabricated URL through the ``url`` parameter.

        Args:
            resource_type(str): the type of resource to be requested. Values must be
                one of the items in Request._resources such as 'data', 'dataflow', 'categoryscheme' etc.
                It is used for URL construction, not to read the received SDMX file.
                Hence, if `fromfile` is given, `resource_type` may be ''.
                Defaults to ''.
            resource_id(str): the id of the resource to be requested.
                It is used for URL construction. Defaults to ''.
            agency(str): ID of the agency providing the data or metadata.
                Used for URL construction only. It tells the SDMX web service
                which agency the requested information originates from. Note that
                an SDMX service may provide information from multiple data providers.
                may be '' if `fromfile` is given. Not to be confused
                with the agency ID passed to :meth:`__init__` which specifies
                the SDMX web service to be accessed.
            key(str, dict): select columns from a dataset by specifying dimension values.
                If type is str, it must conform to the SDMX REST API, i.e. dot-separated dimension values.
                If 'key' is of type 'dict', it must map dimension names to allowed dimension values. Two or more
                values can be separated by '+' as in the str form. The DSD will be downloaded 
                and the items are validated against it before downloading the dataset.  
            params(dict): defines the query part of the URL.
                The SDMX web service guidelines (www.sdmx.org) explain the meaning of
                permissible parameters. It can be used to restrict the
                time range of the data to be delivered (startperiod, endperiod), whether parents, siblings or descendants of the specified
                resource should be returned as well (e.g. references='parentsandsiblings'). Sensible defaults
                are set automatically
                depending on the values of other args such as `resource_type`.
                Defaults to {}.
            headers(dict): http headers. Given headers will overwrite instance-wide headers passed to the
                constructor. Defaults to None, i.e. use defaults 
                from agency configuration
            fromfile(str): path to the file to be loaded instead of
                accessing an SDMX web service. Defaults to None. If `fromfile` is
                given, args relating to URL construction will be ignored.
            tofile(str): file path to write the received SDMX file on the fly. This
                is useful if you want to load data offline using
                `fromfile` or if you want to open an SDMX file in
                an XML editor.
            url(str): URL of the resource to download.
                If given, any other arguments such as
                ``resource_type`` or ``resource_id`` are ignored. Default is None.
            get_footer_url((int, int)): 
                tuple of the form (seconds, number_of_attempts). Determines the
                behavior in case the received SDMX message has a footer where
                one of its lines is a valid URL. ``get_footer_url`` defines how many attempts should be made to
                request the resource at that URL after waiting so many seconds before each attempt.
                This behavior is useful when requesting large datasets from Eurostat. Other agencies do not seem to
                send such footers. Once an attempt to get the resource has been 
                successful, the original message containing the footer is dismissed and the dataset
                is returned. The ``tofile`` argument is propagated. Note that the written file may be
                a zip archive. pandaSDMX handles zip archives since version 0.2.1. Defaults to (30, 3).
            memcache(str): If given, return Response instance if already in self.cache(dict), 
            otherwise download resource and cache Response instance.             
        writer(str): optional custom writer class. 
            Should inherit from pandasdmx.writer.BaseWriter. Defaults to None, 
            i.e. one of the included writers is selected as appropriate.
        dsd(model.DataStructure): DSD to be passed on to the sdmxml reader
            to process a structure-specific dataset without an incidental http request. 

        Returns:
            pandasdmx.api.Response: instance containing the requested
                SDMX Message.

        '''
        # Try to get resource from memory cache if specified
        if memcache in self.cache:
            return self.cache[memcache]

        if url:
            base_url = url
        else:
            # Construct URL from args unless ``tofile`` is given
            # Validate args
            agency = agency or self._agencies[self.agency]['id']
            # Validate resource if no filename is specified
            if not fromfile and resource_type not in self._resources:
                raise ValueError(
                    'resource must be one of {0}'.format(self._resources))
            # resource_id: if it is not a str or unicode type,
            # but, e.g., an invalid Dataflow Definition,
            # extract its ID
            if resource_id and not isinstance(resource_id, (str_type, str)):
                resource_id = resource_id.id
            # Raise error if agency is JSON-based and resource is not supported by the agency.
            # Note that SDMX-JSON currently only supports data messags.
            if (self._agencies[self.agency]['resources'].get('data', {}).get('json')
                    and resource_type != 'data'):
                raise ValueError(
                    'This agency only supports requests for data, not {0}.'.format(resource_type))

            # If key is a dict, validate items against the DSD
            # and construct the key string which becomes part of the URL
            # Otherwise, do nothing as key must be a str confirming to the REST
            # API spec.
            if resource_type == 'data' and isinstance(key, dict):
                # select validation method based on agency capabilities
                if self._agencies[self.agency].get('supports_series_keys_only'):
                    key = self._make_key_from_series(resource_id, key, dsd)
                else:
                    key = self._make_key_from_dsd(resource_id, key)

            # Get http headers from agency config if not given by the caller
            if not (fromfile or headers):
                # Check for default headers
                resource_cfg = self._agencies[self.agency][
                    'resources'].get(resource_type)
                if resource_cfg:
                    headers = resource_cfg.get('headers', {})

            # Construct URL from the given non-empty substrings.
            # if data is requested, omit the agency part. See the query
            # examples
            if resource_type in ['data', 'categoryscheme']:
                agency_id = None
            else:
                agency_id = agency
            if (version is None) and (resource_type != 'data'):
                version = 'latest'
            # Remove None's and '' first. Then join them to form the base URL.
            # Any parameters are appended by remote module.
            if self.agency:
                parts = [self._agencies[self.agency]['url'],
                         resource_type,
                         agency_id,
                         resource_id, version, key]
                base_url = '/'.join(filter(None, parts))

                # Set references to sensible defaults
                params = params.copy()  # to avoid side effects
                if 'references' not in params:
                    if resource_type in [
                            'dataflow', 'datastructure'] and resource_id:
                        params['references'] = 'all'
                    elif resource_type == 'categoryscheme':
                        params['references'] = 'parentsandsiblings'

            elif fromfile:
                base_url = ''
            else:
                raise ValueError(
                    'If `` url`` is not specified, either agency or fromfile must be given.')

        # Now get the SDMX message either via http or as local file
        logger.info(
            'Requesting resource from URL/file %s', (base_url or fromfile))
        source, url, resp_headers, status_code = self.client.get(
            base_url, params=params, headers=headers, fromfile=fromfile)
        if source is None:
            raise SDMXException('Server error:', status_code, url)
        logger.info(
            'Loaded file into memory from URL/file: %s', (url or fromfile))
        # write msg to file and unzip it as required, then parse it
        with source:
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
            # select reader class
            if ((fromfile and fromfile.endswith('.json'))
                    or self._agencies[self.agency]['resources'].get(resource_type, {}).get('json')):
                reader_module = import_module('pandasdmx.reader.sdmxjson')
            else:
                reader_module = import_module('pandasdmx.reader.sdmxml')
            reader_cls = reader_module.Reader
            msg = reader_cls(self, dsd).initialize(source)
        # Check for URL in a footer and get the real data if so configured
        if get_footer_url and hasattr(msg, 'footer'):
            logger.info('Footer found in SDMX message.')
            # Retrieve the first URL in the footer, if any
            url_l = [
                i for i in msg.footer.text if remote.is_url(i)]
            if url_l:
                # found an URL. Wait and try to request it
                footer_url = url_l[0]
                seconds, attempts = get_footer_url
                logger.info(
                    'Found URL in footer. Making %i requests, waiting %i seconds in between.', attempts, seconds)
                for a in range(attempts):
                    sleep(seconds)
                    try:
                        return self.get(tofile=tofile, url=footer_url, headers=headers)
                    except Exception as e:
                        logger.info(
                            'Attempt #%i raised the following exeption: %s', a, str(e))
        # Select default writer
        if not writer:
            if hasattr(msg, 'data'):
                writer = 'pandasdmx.writer.data2pandas'
            else:
                writer = 'pandasdmx.writer.structure2pd'
        r = Response(msg, url, resp_headers, status_code, writer=writer)
        # store in memory cache if needed
        if memcache and r.status_code == 200:
            self.cache[memcache] = r
        return r

    def _make_key_from_dsd(self, flow_id, key):
        '''
        Download the dataflow def. and DSD and validate 
        key(dict) against it. 

        Return: key(str)
        '''
        # get the dataflow and the DSD ID
        dataflow = self.get('dataflow', flow_id,
                            memcache='dataflow' + flow_id)
        dsd_id = dataflow.msg.dataflow[flow_id].structure.id
        dsd_resp = self.get('datastructure', dsd_id,
                            memcache='datastructure' + dsd_id)
        dsd = dsd_resp.msg.datastructure[dsd_id]
        # Extract dimensions excluding the dimension at observation (time, time-period)
        # as we are only interested in dimensions for columns, not rows.
        dimensions = [d for d in dsd.dimensions.aslist() if d.id not in
                      ['TIME', 'TIME_PERIOD']]
        dim_names = [d.id for d in dimensions]
        # Retrieve any ContentConstraint
        try:
            constraint_l = [c for c in dataflow.constraint.aslist()
                            if c.constraint_attachment.id == flow_id]
            if constraint_l:
                constraint = constraint_l[0]
        except:
            constraint = None
        # Validate the key dict
        # First, check correctness of dimension names
        invalid = [d for d in key.keys()
                   if d not in dim_names]
        if invalid:
            raise ValueError(
                'Invalid dimension name {0}, allowed are: {1}'.format(invalid, dim_names))
        # Check for each dimension name if values are correct and construct
        # string of the form 'value1.value2.value3+value4' etc.
        parts = []
        # Iterate over the dimensions. If the key dict
        # contains a value for the dimension, append it to the 'parts' list. Otherwise
        # append ''. Then join the parts to form the dotted str.
        for d in dimensions:
            try:
                values = key[d.id]
                values_l = values.split('+')
                codelist = d.local_repr.enum
                codes = codelist.keys()
                invalid = [v for v in values_l if v not in codes]
                if invalid:
                    # ToDo: attach codelist to exception.
                    raise ValueError("'{0}' is not in codelist for dimension '{1}: {2}'".
                                     format(invalid, d.id, codes))
                # Check if values are in Contentconstraint if present
                if constraint:
                    try:
                        invalid = [
                            v for v in values_l if (d.id, v) not in constraint]
                        if invalid:
                            raise ValueError("'{0}' out of content_constraint for '{1}'.".
                                             format(invalid, d.id))
                    except NotImplementedError:
                        pass
                part = values
            except KeyError:
                part = ''
            parts.append(part)
        return '.'.join(parts)

    def _make_key_from_series(self, flow_id, key, dsd):
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
        all_keys = self.series_keys(flow_id, dsd=dsd)
        dim_names = list(all_keys)
        # Validate the key dict
        # First, check correctness of dimension names
        invalid = [d for d in key
                   if d not in dim_names]
        if invalid:
            raise ValueError(
                'Invalid dimension name {0}, allowed are: {1}'.format(invalid, dim_names))
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
        invalid = list(chain.from_iterable((((k, v) for v in vl if v not in all_keys[k].values)
                                            for k, vl in key_l.items())))
        if invalid:
            raise ValueError("The following dimension values are invalid: {0}".
                             format(invalid))
        # Generate the 'Val1+Val2' notation for multiple dim values and remove the
        # lists
        for k, v in key_l.items():
            key_l[k] = '+'.join(v)
        # assemble the key string which goes into the URL
        parts = [key_l.get(name, '') for name in dim_names]
        return '.'.join(parts)

    def preview_data(self, flow_id, key=None, count=True, total=True, dsd=None):
        '''
        Get keys or number of series for a prospective dataset query allowing for
        keys with multiple values per dimension.
        It downloads the complete list of series keys for a dataflow rather than using constraints and DSD. This feature is,
        however, not supported by all data providers.
        ECB and UNSD are known to work.

        Args:

        flow_id(str): dataflow id

        key(dict): optional key mapping dimension names to values or lists of values.
            Must have been validated before. It is not checked if key values
            are actually valid dimension names and values. Default: {}

        count(bool): if True (default), return the number of series
            of the dataset designated by flow_id and key. If False,
            the actual keys are returned as a pandas DataFrame or dict of dataframes, depending on
            the value of 'total'.

        total(bool): if True (default), return the aggregate number
            of series or a single dataframe (depending on the value of 'count'). If False,
            return a dict mapping keys to dataframes of series keys.
            E.g., if key={'COUNTRY':'IT+CA+AU'}, the dict will
            have 3 items describing the series keys for each country
            respectively. If 'count' is True, dict values will be int rather than
            PD.DataFrame.
        '''
        all_keys = self.series_keys(flow_id, dsd=dsd)
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

            matches = {PartialKey(k): reduce(and_, (key_df.isin({k1: [v1]
                                                                 for k1, v1 in zip(dim_names, k)})[col]
                                                    for col in dim_names))
                       for k in key_product}

            if not count:
                # dict mapping each key to DataFrame with selected key-set
                return {k: all_keys[v] for k, v in matches.items()}
            else:
                # Number of series per key
                return {k: v.value_counts()[True] for k, v in matches.items()}


class Response(object):

    '''Container class for SDMX messages.

    It is instantiated by  .

    Attributes:
        msg(pandasdmx.model.Message): a pythonic representation
            of the SDMX message
        status_code(int): the status code from the http response, if any
        url(str): the URL, if any, that was sent to the SDMX server
        headers(dict): http response headers returned by ''requests''

    Methods:
        write: wrapper around the writer's write method.
            Arguments are propagated to the writer.
    '''

    def __init__(self, msg, url, headers, status_code, writer=None):
        '''
        Set the main attributes and instantiate the writer if given.

        Args:
            msg(pandasdmx.model.Message): the SDMX message
            url(str): the URL, if any, that had been sent to the SDMX server
            headers(dict): http headers 
            status_code(int): the status code returned by the server
            writer(str): the module path for the writer class

        '''
        self.msg = msg
        self.url = url
        self.http_headers = headers
        self.status_code = status_code
        self._init_writer(writer)

    def __getattr__(self, name):
        '''
        Make Message attributes directly readable from Response instance
        '''
        return getattr(self.msg, name)

    def _init_writer(self, writer):
        # Initialize the writer if given
        if writer:
            writer_module = import_module(writer)
            writer_cls = writer_module.Writer
            self._writer = writer_cls(self.msg)
        else:
            self._writer = None

    def write(self, source=None, **kwargs):
        '''Wrappe    r to call the writer's write method if present.

        Args:
            source(pandasdmx.model.Message, iterable): stuff to be written.
                If a :class:`pandasdmx.model.Message` is given, the writer
                itself must determine what to write unless specified in the
                keyword arguments. If an iterable is given,
                the writer should write each item. Keyword arguments may
                specify what to do with the output depending on the writer's API. Defaults to self.msg.

        Returns:
            type: anything the writer returns.
        '''

        if not source:
            source = self.msg
        return self._writer.write(source=source, **kwargs)

    def write_source(self, filename):
        '''
        write xml file by calling the 'write' method of lxml root element.
        Useful to save the xml source file for offline use.
        Similar to passing `tofile` arg to :meth:`Request.get`

        Args:
            filename(str): name/path of target file

        Returns:
            whatever the LXML deserializer returns.
        '''
        return self.msg._reader.write_source(filename)
