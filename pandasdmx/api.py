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
            'url': 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'},
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
                 writer='pandasdmx.writer.data2pandas'):
        '''Set the data provider and writer for an instance.

        Args:

            agency(str): identifier of a data provider.
                Must be one of the dict keys in Request._agencies such as
                'ESTAT', 'ECB' or ''.
                An empty string has the effect that the instance can only
                load data or metadata from files or a pre-fabricated URL. .
                defaults to '', i.e. no agency.

            writer(str): the module path of a writer class, defaults to 'pandasdmx.writer.data2pandas'
        '''
        self.client = remote.REST()
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

    def get(self, resource_type='', resource_id='', agency='', key='', params={},
            fromfile=None, tofile=None, url=None, get_footer_url=(30, 3)):
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

        Returns:
            pandasdmx.api.Response: instance containing the requested
                SDMX Message.

        '''
        if url:
            base_url = url
        else:
            # Construct URL from args unless ``tofile`` is given
            # Validate args
            if not agency:
                agency = self.agency
            # Validate resource if no filename is specified
            if not fromfile and resource_type not in self._resources:
                raise ValueError(
                    'resource must be one of {0}'.format(self._resources))
            # resource_id: if it is not a str or unicode type,
            # but, e.g., a model.DataflowDefinition,
            # extract its ID
            if resource_id and not isinstance(resource_id, (str_type, str)):
                resource_id = resource_id.id

            # Construct URL from the given non-empty substrings.
            # if data is requested, omit the agency part. See the query examples
            # from Eurostat. Hopefully ECB excepts this.
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
        source, url, status_code = self.client.get(
            base_url, params=params, fromfile=fromfile)
        # write msg to file and unzip it as required, then parse it
        with source:
            if tofile:
                with open(tofile, 'wb') as dest:
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
        return Response(msg, url, status_code, writer=self.writer)


class Response(object):

    '''Container class for SDMX messages.

    It is instantiated by  .

    Attributes:
        msg(pandasdmx.model.Message): a pythonic representation
            of the SDMX message
        status_code(int): the status code from the http response, if any
        url(str): the URL, if any, that was sent to the SDMX server

    Methods:
        write: wrapper around the writer's write method.
            Arguments are propagated to the writer.
    '''

    def __init__(self, msg, url, status_code, writer=None):
        '''Set the main attributes and instantiate the writer if given.

        Args:
            msg(pandasdmx.model.Message): the SDMX message
            url(str): the URL, if any, that had been sent to the SDMX server
            status_code(int): the status code returned by the server
            writer(str): the module path for the writer class

        '''
        self.msg = msg
        self.url = url
        self.status_code = status_code
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
