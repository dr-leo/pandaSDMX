"""Network requests API

This module defines two classes: :class:`pandasdmx.api.Request` and
:class:`pandasdmx.api.Response`. Together, these form the high-level API of
:mod:`pandasdmx`. Requesting data and metadata from an SDMX server requires a
good understanding of this API and a basic understanding of the SDMX web
service guidelines (only the chapters on REST services are relevant as
pandasdmx does not support the SOAP interface).

"""
from functools import partial
import logging
from pathlib import Path
from warnings import warn

from pandasdmx import remote
from .model import DataStructureDefinition, MaintainableArtefact
from .reader import get_reader_for_content_type
from .source import NoSource, list_sources, sources
from .util import Resource
import requests

logger = logging.getLogger(__name__)


class Request:
    """Client for a SDMX REST web service.

    Parameters
    ----------
    source : str or :class:`pandasdmx.source.Source`
        Identifier of a data source. If a string, must be one of the known
        sources in :meth:`list_sources`.
    log_level : int
        Override the package-wide logger with one of the
        :ref:`standard logging levels <py:levels>`.
    **session_opts
        Additional keyword arguments are passed to
        :class:`pandasdmx.remote.Session`.

    """
    cache = {}

    #: :class:`pandasdmx.source.Source` for requests sent from the instance.
    source = None

    def __init__(self, source=None, log_level=None, **session_opts):
        """Constructor."""
        try:
            self.source = sources[source.upper()] if source else NoSource
        except KeyError:
            raise ValueError('source must be None or one of: %s' %
                             ' '.join(list_sources()))

        self.session = remote.Session(**session_opts)

        if log_level:
            logging.getLogger('pandasdmx').setLevel(log_level)

    def __getattr__(self, name):
        """Convenience methods."""
        return partial(self.get, Resource[name])

    def __dir__(self):
        """Include convenience methods in dir()."""
        return sorted(super().__dir__() + [ep.name for ep in Resource])

    def clear_cache(self):
        self.cache.clear()

    @property
    def timeout(self):
        return self.session.timeout

    @timeout.setter
    def timeout(self, value):
        self.session.timeout = value

    def series_keys(self, flow_id, use_cache=True):
        """Return all :class:`pandasdmx.model.SeriesKey` for *flow_id*.

        Returns
        -------
        list
        """
        # download an empty dataset with all available series keys
        return self.data(flow_id, params={'detail': 'serieskeysonly'},
                         use_cache=use_cache) \
                   .data[0] \
                   .series \
                   .keys()

    def _make_key(self, resource_type, resource_id, key, dsd=None):
        """Validate *key* if possible.

        If key is a dict, validate items against the DSD and construct the key
        string which becomes part of the URL. Otherwise, do nothing as key must
        be a str confirming to the REST API spec.
        """
        if not (resource_type == Resource.data and isinstance(key, dict)):
            return key

        # Select validation method based on agency capabilities
        if dsd:
            # DSD was provided
            pass
        elif self.source.supports[Resource.datastructure]:
            # Retrieve the DataStructureDefinition
            dsd = self.dataflow(resource_id, params=dict(references='all'),
                                use_cache=True) \
                      .dataflow[resource_id].structure

            if dsd.is_external_reference:
                # DataStructureDefinition was not retrieved with the Dataflow
                # query; retrieve it explicitly
                dsd = self.get(resource=dsd, use_cache=True) \
                          .structure[dsd.id]
        else:
            # Construct a DSD from the keys
            dsd = DataStructureDefinition.from_keys(
                self.series_keys(resource_id))

        # Make a ContentConstraint from the key
        cc = dsd.make_constraint(key)

        return cc.to_query_string(dsd)

    def _request_from_args(self, **kwargs):
        """Validate arguments and prepare pieces for a request."""
        parameters = kwargs.pop('params', {})
        headers = kwargs.pop('headers', {})

        # Base URL
        url_parts = [self.source.url]

        # Resource arguments
        resource = kwargs.pop('resource', None)
        resource_type = kwargs.pop('resource_type', None)
        resource_id = kwargs.pop('resource_id', None)

        try:
            if resource_type:
                resource_type = Resource[resource_type]
        except KeyError:
            raise ValueError(f'resource_type ({resource_type!r}) must be in '
                             + Resource.describe())

        if resource:
            # Resource object is given
            assert isinstance(resource, MaintainableArtefact)

            # Class of the object
            if resource_type:
                assert resource_type == Resource.from_obj(resource)
            else:
                resource_type = Resource.from_obj(resource)
            if resource_id:
                assert resource_id == resource.id, (
                    f'mismatch between resource_id={resource_id!r} and '
                    f'resource={resource!r}')
            else:
                resource_id = resource.id

        force = kwargs.pop('force', False)
        if not (force or self.source.supports[resource_type]):
            raise NotImplementedError(f'{self.source.id} does not support the'
                                      f'{resource_type!r} API endpoint; '
                                      'override using force=True')

        url_parts.append(resource_type.name)

        # Data provider ID to use in the URL
        provider = kwargs.pop('provider', None)
        if resource_type == Resource.data:
            # Requests for data do not specific an agency in the URL
            if provider is not None:
                warn(f"'provider' argument is redundant for {resource_type!r}")
            provider_id = None
        else:
            provider_id = provider if provider else getattr(self.source, 'id',
                                                            None)

        url_parts.extend([provider_id, resource_id])

        version = kwargs.pop('version', None)
        if not version and resource_type != Resource.data:
            url_parts.append('latest')

        key = kwargs.pop('key', None)
        dsd = kwargs.pop('dsd', None)
        if kwargs.pop('validate', True):
            key = self._make_key(resource_type, resource_id, key, dsd)

        url_parts.append(key)

        # Assemble final URL
        url = '/'.join(filter(None, url_parts))

        # Parameters: set 'references' to sensible defaults
        if 'references' not in parameters:
            if resource_type in [Resource.dataflow, Resource.datastructure] \
                    and resource_id:
                parameters['references'] = 'all'
            elif resource_type == Resource.categoryscheme:
                parameters['references'] = 'parentsandsiblings'

        # Headers: use headers from source config if not given by the caller
        if not headers and self.source and resource_type:
            headers = self.source.headers.get(resource_type.name, {})

        if len(kwargs):
            raise ValueError(f'unrecognized arguments: {kwargs!r}')

        return requests.Request('get', url, params=parameters,
                                headers=headers)

    def _request_from_url(self, url, **kwargs):
        parameters = kwargs.pop('params', {})
        headers = kwargs.pop('headers', {})

        if len(kwargs):
            raise ValueError(f'unrecognized arguments: {kwargs!r}')

        return requests.Request('get', url, params=parameters,
                                headers=headers)

    def get(self, resource_type=None, resource_id=None, tofile=None,
            use_cache=False, dry_run=False, **kwargs):
        """Retrieve SDMX data or metadata.

        (Meta)data is retrieved from the :attr:`source` of the current Request.
        The item(s) to retrieve can be specified in one of two ways:

        1. `resource_type`, `resource_id`: These give the type (see
           :class:`Resource`) and, optionally, ID of the item(s). If the
           `resource_id` is not given, all items of the given type are
           retrieved.
        2. a `resource` object, i.e. a :class:`MaintainableArtefact
           <pandasdmx.model.MaintainableArtefact>`: `resource_type` and
           `resource_id` are determined by the object's class and :attr:`id
           <pandasdmx.model.IdentifiableArtefact.id>` attribute, respectively.

        Data is retrieved with `resource_type='data'`. In this case, the
        optional keyword argument `key` can be used to constrain the data that
        is retrieved. Examples of the formats for `key`:

        1. ``{'GEO': ['EL', 'ES', 'IE']}``: :class:`dict` with dimension
           name(s) mapped to an iterable of allowable values.
        2. ``{'GEO': 'EL+ES+IE'}``: :class:`dict` with dimension name(s)
           mapped to strings joining allowable values with `'+'`, the logical
           'or' operator for SDMX web services.
        3. ``'....EL+ES+IE'``: :class:`str` in which ordered dimension values
           (some empty, ``''``) are joined with ``'.'``. Using this form
           requires knowledge of the dimension order in the target data
           `resource_id`; in the example, dimension 'GEO' is the fifth of five
           dimensions: ``'.'.join(['', '', '', '', 'EL+ES+IE'])``.
           :meth:`CubeRegion.to_query_string
           <pandasdmx.model.CubeRegion.to_query_string>` can also be used to
           create properly formatted strings.

        For formats 1 and 2, but not 3, the `key` argument is validated against
        the relevant :class:`DataStructureDefinition
        <pandasdmx.model.DataStructureDefinition>`, either given with the `dsd`
        keyword argument, or retrieved from the web service before the main
        query.

        For the optional `param` keyword argument, some useful parameters are:

        - 'startperiod', 'endperiod': restrict the time range of data to
          retrieve.
        - 'references': control which item(s) related to a metadata resource
          are retrieved, e.g. `references='parentsandsiblings'`.

        Parameters
        ----------
        resource_type : str or :class:`Resource`, optional
            Type of resource to retrieve.
        resource_id : str, optional
            ID of the resource to retrieve.
        tofile : str or :py:class:`os.PathLike`, optional
            File path to write SDMX data as it is recieved.
        use_cache : bool, optional
            If :obj:`True`, return a previously retrieved :class:`Message` from
            :attr:`cache`, or update the cache with a newly-retrieved Message.
        dry_run : bool, optional
            If :obj:`True`, prepare and return a :class:`requests.Request`
            object, but do not execute the query. The prepared URL and headers
            can be examined by inspecting the returned object.
        **kwargs
            Other, optional parameters (below).

        Other Parameters
        ----------------
        dsd : :class:`DataStructureDefinition \
                      <pandasdmx.model.DataStructureDefinition>`
            Existing object used to validate the `key` argument. If not
            provided, an additional query executed to retrieve a DSD in order
            to validate the `key`.
        force : bool
            If :obj:`True`, execute the query even if the :attr:`source` does
            not support queries for the given `resource_type`. Default:
            :obj:`False`.
        headers : dict
            HTTP headers. Given headers will overwrite instance-wide headers
            passed to the constructor. Default: :obj:`None` to use the default
            headers of the :attr:`source`.
        key : str or dict
            For queries with `resource_type='data'`. :class:`str` values are
            not validated; :class:`dict` values are validated using
            :meth:`DataStructureDefinition.make_constraint
            <pandasdmx.model.DataStructureDefinition.make_constraint>`.
        params : dict
            Query parameters. The `SDMX REST web service guidelines <https://\
            github.com/sdmx-twg/sdmx-rest/tree/master/v2_1/ws/rest/docs>`_
            describe parameters and allowable values for different queries.
            `params` is not validated before the query is executed.
        provider : str
            ID of the agency providing the data or metadata. Default:
            ID of the :attr:`source` agency.

            An SDMX web service is a ‘data source’ operated by a specific,
            ‘source’ agency. A web service may host data or metadata originally
            published by one or more ‘provider’ agencies. Many sources are also
            providers. Other agencies—e.g. the SDMX Global Registry—simply
            aggregate (meta)data from other providers, but do not providing any
            (meta)data themselves.
        resource : :mod:`MaintainableArtefact \
                         <pandasdmx.model.MaintainableArtefact>` subclass
            Object to retrieve. If given, `resource_type` and `resource_id` are
            ignored.
        version : str
            :attr:`version <pandasdmx.model.VersionableArtefact.version>`
            of a resource to retrieve. Default: the keyword 'latest'.

        Returns
        -------
        :class:`pandasdmx.message.Message` or :class:`requests.Request`
            The requested SDMX message or, if `dry_run` is :obj:`True`, the
            prepared request object.

        Raises
        ------
        NotImplementedError
            If the :attr:`source` does not support the given `resource_type`
            and `force` is not :obj:`True`.

        """
        # Allow sources to modify request args
        # TODO this should occur after most processing, defaults, checking etc.
        #      are performed, so that core code does most of the work.
        if self.source:
            self.source.modify_request_args(kwargs)

        if 'url' in kwargs:
            req = self._request_from_url(**kwargs)
        else:
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
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise e from None
        except requests.exceptions.HTTPError as e:
            # Convert a 501 response to a Python NotImplementedError
            if e.response.status_code == 501:
                raise NotImplementedError(
                    '{!r} endpoint at {}'.format(resource_type, e.request.url))
            else:
                raise

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

        # Call the finish_message() hook
        msg = self.source.finish_message(msg, self, **kwargs)

        # store in memory cache if needed
        if use_cache:
            self.cache[req.url] = msg

        return msg

    def preview_data(self, flow_id, key={}):
        """Return a preview of data.

        For the Dataflow *flow_id*, return all series keys matching *key*.
        preview_data() uses a feature supported by some data providers that
        returns :class:`SeriesKeys <pandasdmx.model.SeriesKey>` without the
        corresponding :class:`Observations <pandasdmx.model.Observation>`.

        To count the number of series::

            keys = sdmx.Request('PROVIDER').preview_data('flow')
            len(keys)

        To get a :mod:`pandas` object containing the key values::

            keys_df = sdmx.to_pandas(keys)

        Parameters
        ----------
        flow_id : str
            Dataflow to preview.
        key : dict, optional
            Mapping of *dimension* to *values*, where *values* may be a
            '+'-delimited list of values. If given, only SeriesKeys that match
            *key* are returned. If not given, preview_data is equivalent to
            ``list(req.series_keys(flow_id))``.

        Returns
        -------
        list of :class:`SeriesKey <pandasdmx.model.SeriesKey>`
        """
        # Retrieve the series keys
        all_keys = self.series_keys(flow_id)

        if len(key):
            # Construct a DSD from the keys
            dsd = DataStructureDefinition.from_keys(all_keys)

            # Make a ContentConstraint from *key*
            cc = dsd.make_constraint(key)

            # Filter the keys
            return [k for k in all_keys if k in cc]
        else:
            # No key is provided
            return list(all_keys)


def read_sdmx(filename_or_obj, format=None):
    """Load a SDMX-ML or SDMX-JSON message from a file or file-like object.

    Parameters
    ----------
    filename_or_obj : str or os.PathLike or file
    format: 'XML' or 'JSON', optional
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
    except KeyError:
        if format:
            reader = readers[format]
            obj = open(str(filename_or_obj))
        else:
            msg = ("cannot identify SDMX message format from file name "
                   f"'{filename_or_obj.name}'; use  format='...'")
            raise RuntimeError(msg)
    except AttributeError:
        # File is already open

        # Read a line and then return the cursor to the initial position
        pos = filename_or_obj.tell()
        first_line = filename_or_obj.readline().strip()
        filename_or_obj.seek(pos)

        if first_line.startswith('{'):
            reader = readers['JSON']
        elif first_line.startswith('<'):
            reader = readers['XML']
        else:
            msg = f"cannot infer SDMX message format from '{first_line[:5]}..'"
            raise RuntimeError(msg)

        obj = filename_or_obj

    return reader().read_message(obj)


def read_url(url, **kwargs):
    """Request a URL directly."""
    return Request().get(url=url, **kwargs)
