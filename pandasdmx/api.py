"""Network requests API

This module defines two classes: :class:`pandasdmx.api.Request` and
:class:`pandasdmx.api.Response`. Together, these form the high-level API of
:mod:`pandasdmx`. Requesting data and metadata from an SDMX server requires a
good understanding of this API and a basic understanding of the SDMX web
service guidelines (only the chapters on REST services are relevant as
pandasdmx does not support the SOAP interface).

"""
from functools import partial, reduce
from itertools import product
import logging
from operator import and_
from pathlib import Path
import sys
from warnings import warn

from pandasdmx import remote
from pandasdmx.model import DataStructureDefinition, IdentifiableArtefact
from pandasdmx.reader import get_reader_for_content_type
from pandasdmx.source import list_sources, sources
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
    source : str
        Identifier of a data source. Must be one of the dict keys in
        Request._agencies such as 'ESTAT', 'ECB', ''GSR' or ''. If '', the
        instance can only retrieve data or metadata from pre-fabricated URLs
        provided to :meth:`get`.
    log_level : int
        Override the package-wide logger with one of the
        :ref:`standard logging levels <py:levels>`.
    **session_opts
        Additional keyword arguments are passed to
        :class:`pandasdmx.remote.Session`.

    """
    cache = {}
    _resources = ['dataflow', 'datastructure', 'data', 'categoryscheme',
                  'codelist', 'conceptscheme', 'contentconstraint']

    @classmethod
    def _make_get_wrappers(cls):
        for r in cls._resources:
            setattr(cls, r, ResourceGetter(r))

    @classmethod
    def url(cls, url, **kwargs):
        """Request a URL directly."""
        return Request().get(url=url, **kwargs)

    def __init__(self, source=None, log_level=None, **session_opts):
        """Constructor."""
        # If needed, generate wrapper properties for get method
        if not hasattr(self, 'data'):
            self._make_get_wrappers()

        try:
            self.source = source if source is None else sources[source.upper()]
        except KeyError:
            raise ValueError('source must be None or one of: %s' %
                             ' '.join(list_sources()))

        self.session = remote.Session(**session_opts)

        if log_level:
            logging.getLogger('pandasdmx').setLevel(log_level)

    def clear_cache(self):
        self.cache.clear()

    @property
    def timeout(self):
        return self.session.timeout

    @timeout.setter
    def timeout(self, value):
        self.session.timeout = value

    def series_keys(self, flow_id, use_cache=True):
        """Get an empty dataset with all possible series keys.

        Return a pandas DataFrame. Each column represents a dimension, each row
        a series key of datasets of the given dataflow.
        """
        # download an empty dataset with all available series keys
        resp = self.data(flow_id, params={'detail': 'serieskeysonly'},
                         use_cache=use_cache)

        return DataStructureDefinition.from_keys(resp.data[0].series.keys())

    def _make_key(self, resource_type, resource_id, key):
        """Validate *key* if possible.

        If key is a dict, validate items against the DSD and construct the key
        string which becomes part of the URL. Otherwise, do nothing as key must
        be a str confirming to the REST API spec.
        """
        if not (resource_type == 'data' and isinstance(key, dict)):
            return key

        # Select validation method based on agency capabilities
        if self.source.supports['datastructure']:
            # Retrieve the DataflowDefinition
            df = self.get('dataflow', resource_id, use_cache=True) \
                     .dataflow[resource_id]

            # Retrieve the DataStructureDefinition
            dsd_id = df.structure.id
            dsd = self.get('datastructure', dsd_id, use_cache=True) \
                      .structure[dsd_id]
        else:
            # Construct a DSD from the keys
            dsd = self.series_keys(resource_id)

        # Make a ContentConstraint from the key
        cc = dsd.make_constraint(key)

        # TODO check that keys match dataflow constraints

        return cc.to_query_string(dsd)

    def _request_from_args(self, **kwargs):
        """Validate arguments and prepare pieces for a request."""
        # Allow sources to modify request args
        # TODO this should occur after most processing, defaults, checking etc.
        #      are performed, so that core code does most of the work.
        if self.source:
            self.source.modify_request_args(kwargs)

        parameters = kwargs.pop('params', {})
        headers = kwargs.pop('headers', {})

        # Base URL
        direct_url = kwargs.pop('url', None)
        if not direct_url:
            url_parts = [self.source.url]
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

        if resource_type and not self.source.supports[resource_type]:
            raise ValueError("{} does not support the '{}' API endpoint"
                             .format(self.source.id, resource_type))

        force = kwargs.pop('force', False)
        try:
            supported = direct_url or self.source.supports[resource_type]
        except KeyError:
            raise ValueError("resource_type ('%s') must be in %r" %
                             (resource_type, self._resources))
        if not (force or supported):
            raise NotImplementedError("%s does not support %s queries; try "
                                      "force=True" % (self.source.id,
                                                      resource_type))

        if not direct_url:
            url_parts.append(resource_type)

        # Agency ID to use in the URL
        agency = kwargs.pop('agency', None)
        if resource_type == 'data':
            # Requests for data do not specific an agency in the URL
            if agency is not None:
                warn("agency argument is redundant for resource type '{}'"
                     .format(resource_type))
            agency_id = None
        else:
            agency_id = agency if agency else getattr(self.source, 'id', None)

        if not direct_url:
            url_parts.extend([agency_id, resource_id])

        version = kwargs.pop('version', None)
        if not version and resource_type != 'data' and not direct_url:
            url_parts.append('latest')

        key = kwargs.pop('key', None)
        if kwargs.pop('validate', True):
            url_parts.append(self._make_key(resource_type, resource_id, key))
        else:
            url_parts.append(key)

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
        if not headers and self.source:
            headers = self.source.headers.get(resource_type, {})

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
        resource_type : str
            Type of resource to be requested. Values must be one of the items
            in Request._resources such as 'data', 'dataflow', 'categoryscheme',
            etc. It is used for URL construction, not to read the received SDMX
            file. Default: ''.
        resource_id : str
            ID of the resource to be requested. It is used for URL
            construction. Defaults to ''.
        agency : str
            ID of the agency providing the data or metadata.
            Used for URL construction only. It tells the SDMX web service
            which agency the requested information originates from. Note
            that an SDMX service may provide information from multiple data
            providers.
            Not to be confused with the data source ID passed to
            :meth:`__init__` which specifies the SDMX web service to be
            accessed.
        key : str or dict
            Select columns from a dataset by specifying dimension values.
            If type is str, it must conform to the SDMX REST API, i.e.
            dot-separated dimension values.
            If 'key' is of type 'dict', it must map dimension names to
            allowed dimension values. Two or more values can be separated
            by '+' as in the str form. The DSD will be downloaded and the
            items are validated against it before downloading the dataset.
        params : dict
            Query part of the URL.
            The SDMX web service guidelines (www.sdmx.org) explain the
            meaning of permissible parameters. It can be used to restrict
            the time range of the data to be delivered (startperiod,
            endperiod), whether parents, siblings or descendants of the
            specified resource should be returned as well (e.g.
            references='parentsandsiblings'). Sensible defaults are set
            automatically depending on the values of other args such as
            `resource_type`. Defaults to {}.
        headers : dict
            HTTP headers. Given headers will overwrite
            instance-wide headers passed to the constructor. Defaults to
            `None`, i.e. use defaults from agency configuration.
        tofile : str or :py:class:`os.PathLike`
            File path to write the received SDMX file on the fly. This is
            useful if you want to load data offline using `open_file()` or if
            you want to open an SDMX file in an XML editor.
        url : str
            URL of the resource to download.
            If given, any other arguments such as `resource_type` or
            `resource_id` are ignored. Default is None.
        get_footer_url : (int, int)
            Tuple of the form (seconds, number_of_attempts). Determines the
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
        memcache : str
            If given, return Response instance if already in
            self.cache(dict), otherwise download resource and cache
            Response instance.

        Returns
        -------
        :class:`pandasdmx.message.Message` or subclass
            The requested SDMX message.

        """
        req = self._request_from_args(
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs)
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

        try:
            response = self.session.send(req)
        except requests.exceptions.ConnectionError as e:
            raise e from None

        response.raise_for_status()

        # Maybe copy the response to file as it's received
        arg = [tofile] if tofile else []
        response_content = remote.ResponseIO(response, *arg)

        # Select reader class
        content_type = response.headers.get('content-type', None)
        try:
            Reader = get_reader_for_content_type(content_type)
        except ValueError:
            try:
                response, response_content = self.source.handle_response(
                    response, response_content)
                content_type = response.headers.get('content-type', None)
                Reader = get_reader_for_content_type(content_type)
            except ValueError:
                raise ValueError("can't determine a reader for response "
                                 "content type: %s" % content_type)

        # Instantiate reader
        reader = Reader()

        # Parse the message
        msg = reader.read_message(response_content)

        # Store the HTTP response with the message
        msg.response = response

        msg = self.source.finish_message(msg, self,
                                         get_footer_url=get_footer_url)

        # store in memory cache if needed
        if use_cache:
            self.cache[req.url] = msg

        return msg

    def preview_data(self, flow_id, key=None, count=True, total=True):
        """
        Get keys or number of series for a prospective dataset query allowing
        for keys with multiple values per dimension. It downloads the complete
        list of series keys for a dataflow rather than using constraints and
        DSD. This feature is, however, not supported by all data providers.
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
        key_l = self.prepare_key(key)
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
        # str() here is for Python 3.5 compatibility
        obj = open(str(filename_or_obj))
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

        obj = filename_or_obj

    return reader().read_message(obj)
