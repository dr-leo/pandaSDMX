# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>, all rights reserved


'''
This module defines two classes: :class:`pandasdmx.api.Request` and :class:`pandasdmx.api.Response`.
Together, these form the high-level API of :mod:`pandasdmx`. Requesting data and metadata from
an SDMX server requires a good understanding of this API and a basic understanding of the SDMX web service guidelines
only the chapters on REST services are relevant as pandasdmx does not support the
SOAP interface.

'''


from pandasdmx import remote
from pandasdmx.utils import str_type
from pandasdmx.reader.sdmxml import SDMXMLReader
from importlib import import_module
from zipfile import ZipFile, is_zipfile
from time import sleep

__all__ = ['Request']


class Request(object):

    """Get SDMX data and metadata from remote servers or local files.
    """

    _agencies = {
        '': None,  # empty agency for convenience when fromfile is given.
        'ESTAT': {
            'name': 'Eurostat',
            'url': 'http://ec.europa.eu/eurostat/SDMX/diss-web/rest'},
        'ECB': {
            'name': 'European Central Bank',
            'url': 'http://sdw-wsrest.ecb.int/service'},
        'SGR': {
            'name': 'SDMX Global Registry',
            'url': 'https://registry.sdmx.org/ws/rest'},
    }

    _resources = ['dataflow', 'datastructure', 'data', 'categoryscheme',
                  'categorisation', 'codelist', 'conceptscheme']

    def __init__(self, agency='',
                 writer='pandasdmx.writer.data2pandas', cache=None,
                 **http_cfg):
        '''
        Set the SDMX agency, writer, and configure http requests.

        Args:

            agency(str): identifier of a data provider.
                Must be one of the dict keys in Request._agencies such as
                'ESTAT', 'ECB', ''GSR' or ''.
                An empty string has the effect that the instance can only
                load data or metadata from files or a pre-fabricated URL. .
                defaults to '', i.e. no agency.

            writer(str): the module path of a writer class, defaults to 'pandasdmx.writer.data2pandas'
            cache(dict): args to be passed on to 
                ``requests_cache.install_cache()``. Default is None (no caching).

            **http_cfg: used to configure http requests. E.g., you can 
            specify proxies, authentication information and more.
            See also the docs of the ``requests`` package at 
            http://www.python-requests.org/en/latest/.   
        '''
        self.client = remote.REST(cache, http_cfg)
        self.agency = agency
        self.writer = writer

    def get_reader(self):
        '''get a Reader instance. Called by :meth:`get`.'''
        return SDMXMLReader(self)

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
        self.cache = {}  # for SDMX messages

    def clear_cache(self):
        self.cache.clear()

    def get(self, resource_type='', resource_id='', agency='', key='', params=None,
            fromfile=None, tofile=None, url=None, get_footer_url=(30, 3),
            memcache=None):
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
            if params is None:
                params = {}
            if not agency:
                agency = self.agency
            # Validate resource if no filename is specified
            if not fromfile and resource_type not in self._resources:
                raise ValueError(
                    'resource must be one of {0}'.format(self._resources))
            # resource_id: if it is not a str or unicode type,
            # but, e.g., a invalid DataflowDefinition,
            # extract its ID
            if resource_id and not isinstance(resource_id, (str_type, str)):
                resource_id = resource_id.id

            # If key is a dict, validate items against the DSD
            # and construct the key string which becomes part of the URL
            # Otherwise, do nothing as key must be a str confirming to the REST
            # API spec.
            if resource_type == 'data' and isinstance(key, dict):
                key = self.make_key(resource_id, key)

            # Construct URL from the given non-empty substrings.
            # if data is requested, omit the agency part. See the query
            # examples
            if resource_type in ['data', 'categoryscheme']:
                agency = ''
            # Remove None's and '' first. Then join them to form the base URL.
            # Any parameters are appended by remote module.
            if self.agency:
                parts = [self._agencies[self.agency]['url'],
                         resource_type, agency, resource_id, key]
                base_url = '/'.join(filter(None, parts))

                # Set references to sensible defaults
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
        source, url, headers, status_code = self.client.get(
            base_url, params=params, fromfile=fromfile)
        # write msg to file and unzip it as required, then parse it
        with source:
            if tofile:
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
            msg = self.get_reader().initialize(source)
        # Check for URL in a footer and get the real data if so configured
        if get_footer_url and hasattr(msg, 'footer'):
            # Retrieve the first URL in the footer, if any
            url_l = [
                i for i in msg.footer.text if remote.requests.utils.urlparse(i).scheme]
            if url_l:
                # found an URL. Wait and try to request it
                footer_url = url_l[0]
                seconds, attempts = get_footer_url
                for a in range(attempts):
                    sleep(seconds)
                    try:
                        return self.get(tofile=tofile, url=footer_url)
                    except Exception:
                        pass
        r = Response(msg, url, headers, status_code, writer=self.writer)
        # store in memory cache if needed
        if memcache and r.status_code == 200:
            self.cache[memcache] = r
        return r

    def make_key(self, flow_id, key):
        '''
        Download the dataflow def. and DSD and validate 
        key(dict) against it. 

        Return: key(str)
        '''
        # get the dataflow to thus the DSD ID
        dataflow = self.get('dataflow', flow_id,
                            memcache='dataflow' + flow_id)
        dsd_id = dataflow.msg.dataflows[flow_id].structure.id
        dsd_resp = self.get('datastructure', dsd_id,
                            memcache='datastructure' + dsd_id)
        dsd = dsd_resp.msg.datastructures[dsd_id]
        # Extract dimensions excluding the dimension at observation (time, time-period)
        # as we are only interested in dimensions for columns, not rows.
        dimensions = [d for d in dsd.dimensions.aslist() if d.id not in
                      ['TIME', 'TIME_PERIOD']]
        dim_names = [d.id for d in dimensions]
        # Retrieve any ContentConstraint
        try:
            constraint_l = [c for c in dataflow.msg.constraints.aslist()
                            if c.constraint_attachment.id == flow_id]
            if constraint_l:
                constraint = constraint_l[0]
        except Exception:
            constraint = None
        # Validate the key dict
        # First, check correctness of dimension names
        invalid = [d for d in key.keys()
                   if d not in dim_names]
        if invalid:
            raise ValueError(
                'Invalid dimension name {0}, allowed are: '.format(invalid, dim_names))
        # Check for each dimension name if values are correct and construct
        # of the form 'value1.value2.value3+value4' etc.
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
                    raise ValueError("'{0}' is not in codelist for dimension '{1}'".
                                     format(invalid, d.id))
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
        '''Set the main attributes and instantiate the writer if given.

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
        if hasattr(self.msg, 'data'):
            self.init_writer(writer)

    def init_writer(self, writer):
        # Initialize the writer if given
        if writer:
            writer_module = import_module(writer)
            writer_cls = writer_module.Writer
            self._writer = writer_cls(self.msg)
        else:
            self._writer = None

    def write(self, source=None, **kwargs):
        '''Wrapper to call the writer's write method if present.

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
