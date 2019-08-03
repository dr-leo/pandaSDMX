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
from .model import DataStructureDefinition, IdentifiableArtefact
from .reader import get_reader_for_content_type
from .source import NoSource, list_sources, sources
from .util import Resource
import requests

logger = logging.getLogger(__name__)


class Request:
    """Client for a SDMX data provider.

    Parameters
    ----------
    source : str or :obj:`None`
        Identifier of a data source. If a string, must be one of the known
        sources in :meth:`list_sources`. If :obj:`None`, the Request instance
        can only retrieve data or metadata from complete URLs provided to
        :meth:`get`.
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

    @classmethod
    def url(cls, url, **kwargs):
        """Request a URL directly."""
        return Request().get(url=url, **kwargs)

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
            # Retrieve the DataflowDefinition
            df = self.get('dataflow', resource_id, use_cache=True) \
                     .dataflow[resource_id]

            # Retrieve the DataStructureDefinition
            dsd_id = df.structure.id
            dsd = self.get('datastructure', dsd_id, use_cache=True) \
                      .structure[dsd_id]
        else:
            # Construct a DSD from the keys
            dsd = DataStructureDefinition.from_keys(
                self.series_keys(resource_id))

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
        url_parts = [direct_url] if direct_url else [self.source.url]

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
            assert isinstance(resource, IdentifiableArtefact)

            # Class of the object
            if resource_type:
                assert resource_type == Resource[resource]
            else:
                resource_type = Resource[resource]
            if resource_id:
                assert resource_id == resource.id, (
                    f'mismatch between resource_id={resource_id!r} and '
                    f'resource={resource!r}')
            else:
                resource_id = resource.id

        force = kwargs.pop('force', False)
        if not (force or direct_url or self.source.supports[resource_type]):
            raise NotImplementedError(f'{self.source.id} does not support the'
                                      f'{resource_type!r} API endpoint; '
                                      'override using force=True')

        if not direct_url:
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

        if not direct_url:
            url_parts.extend([provider_id, resource_id])

        version = kwargs.pop('version', None)
        if not version and (resource_type != Resource.data
                            and not direct_url):
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

        assert len(kwargs) == 0, ValueError('unrecognized arguments: %r' %
                                            kwargs)

        return requests.Request('get', url, params=parameters,
                                headers=headers)

    def get(self, resource_type=None, resource_id=None, tofile=None,
            use_cache=False, dry_run=False, **kwargs):
        """Retrieve SDMX data or metadata.

        get() constructs and queries URLs for the :attr:`source` of the current
        Request, *except* if the `url` parameter is given.

        Parameters
        ----------
        resource_type : str or :class:`Resource`, optional
            Type of resource to get.
        resource_id : str, optional
            ID of the resource to get.
        provider : str, optional
            ID of the agency providing the data or metadata. Default:
            ID of the same agency as :attr:`source`.

            The agency that operates an SDMX web service is the ‘source’ agency
            (associated with :attr:`source`); a web service may host data or
            metadata originally published by one or more ‘provider’ agencies.
            Many sources are also providers; but other agencies—e.g. the SDMX
            Global Registry—simply aggregate (meta)data from other providers
            without providing any (meta)data of their own.
        tofile : str or :py:class:`os.PathLike`, optional
            File path to write SDMX data as it is recieved.
        use_cache : bool, optional
            If :obj:`True`, return a previously retrieved :class:`Message` from
            :attr:`cache`, or update the cache with a newly-retrieved Message.
        dry_run : bool, optional
            If :obj:`True`, prepare and return a :class:`requests.Request`
            object, but do not execute the query. The prepared URL and headers
            can be examined by inspecting the returned object.
        force : bool, optional
            If :obj:`True`, execute the query even if the :attr:`source` does
            not support queries for the given `resource_type`.
        **kwargs
            Other parameters (below) used to construct the query URL.

        Other Parameters
        ----------------
        resource : :mod:`pandasdmx.model` object
            Object to get.
        url : str
            Full URL to get directly. If given, other arguments are ignored.
            See also :meth:`url`.
        key : str or dict
            Select columns from a dataset by specifying dimension values. If
            type is str, it must conform to the SDMX REST API, i.e. dot-
            separated dimension values. If 'key' is of type 'dict', it must map
            dimension names to allowed dimension values. Two or more values can
            be separated by '+' as in the str form. The DSD will be downloaded
            and the items are validated against it before downloading the
            dataset.
        params : dict
            Query part of the URL. The SDMX web service guidelines
            (www.sdmx.org) explain the meaning of permissible parameters. It
            can be used to restrict the time range of the data to be delivered
            (startperiod, endperiod), whether parents, siblings or descendants
            of the specified resource should be returned as well (e.g.
            references='parentsandsiblings'). Sensible defaults are set
            automatically depending on the values of other args such as
            `resource_type`. Defaults to {}.
        headers : dict
            HTTP headers. Given headers will overwrite instance-wide headers
            passed to the constructor. Defaults to `None`, i.e. use defaults
            from agency configuration.
        dsd : :class:`DataStructureDefinition`
        version : str

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


def open_file(filename_or_obj, format=None):
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
            raise RuntimeError(('unable to identify SDMX file format from '
                                'name "{}"; use format="..."')
                               .format(filename_or_obj.name))
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
