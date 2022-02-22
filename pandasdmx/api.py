"""Network requests API.

This module defines :class:`.Request`, which forms the high-level API of
:mod:`pandasdmx`. Requesting data and metadata from an SDMX server requires a
understanding of this API and a basic understanding of the SDMX web service
guidelines.
"""
import logging
from functools import partial
from typing import Dict
from warnings import warn

import requests

from . import remote
from .reader import get_reader_for_content_type
from .message import Message
from pandasdmx import model
from .model import DataStructureDefinition, MaintainableArtefact, ValidationLevels
from .source import NoSource, list_sources, sources
from .util import Resource

logger = logging.getLogger(__name__)


class Request:
    """Client for a SDMX REST web service.

    Parameters:
    
    source : str or source.Source
        Identifier of a data source. If a string, must be one of the known
        sources in :meth:`list_sources`.
    log_level : int
        Override the package-wide logger with one of the
        :ref:`standard logging levels <py:levels>`.
    session : optional instance of :class:`requests.Session`, 
        or  a subclass. If given,
        it is  used for HTTP requests, 
        and any   *session_opts* passed  will raise TypeError. 
        A typical  use case is the injection of alternative 
        caching libraries such as Cache Control.
    timeout : float or 2-tuple. 
        It is stored as :attr:`Request.timeout`. It is  passed on to each 
        HTTP request to an SDMX source. Default is 30.1.
        If it is a float, it denotes the 
        number of seconds to wait
        for a response from the server. 
        See the docs for the`requests` library for more details.    
    session_opts :
        Additional keyword arguments are passed to
        :class:`.Session`. Typical uses are to specify proxies, auth or cert.
    """

    cache: Dict[str, Message] = {}

    #: :class:`.source.Source` for requests sent from the instance.
    source = None

    #: :class:`.Session` for queries sent from the instance.
    session = None

    def __init__(
        self, source=None, log_level=None, session=None, timeout=30.1, **session_opts
    ):
        """Constructor."""
        self.timeout = timeout
        try:
            self.source = sources[source.upper()] if source else NoSource
        except KeyError:
            raise ValueError(
                "source must be None or one of: %s" % " ".join(list_sources())
            )

        if session and session_opts:
            raise TypeError("When `session` is given, `session_opts` must be  empty.")
        self.session = session or remote.Session(**session_opts)

        if log_level:
            logging.getLogger("pandasdmx").setLevel(log_level)

    @property
    def default_locale(self):
        """
        Return global default locale
        for international strings
        used, eg. by writers 
        """
        return model.DEFAULT_LOCALE

    @default_locale.setter
    def default_locale(self, locale):
        model.DEFAULT_LOCALE = locale

    @property
    def validation_level(self):
        """
        Return current validation level.  
        """
        return model.DEFAULT_VAL_LEVEL

    @validation_level.setter
    def validation_level(self, level):
        model.DEFAULT_VAL_LEVEL = ValidationLevels[level]

    def __getattr__(self, name):
        """Convenience methods."""
        try:
            # Provide resource_type as a positional argument, so that the
            # first positional argument to the convenience method is treated as
            # resource_id
            func = partial(self.get, Resource[name])
        except KeyError:
            raise AttributeError(name)
        else:
            # Modify the docstring to explain the argument fixed by the
            # convenience method
            func.__doc__ = self.get.__doc__.replace(
                ".\n", f" with resource_type={repr(name)}.\n", 1
            )
            return func

    def __dir__(self):
        """Include convenience methods in dir()."""
        return super().__dir__() + [ep.name for ep in Resource]

    def view_doc(self):
        """
        Open documentation website of the data source, if given, in a new browser tab.
        Otherwise, raise RuntimeError.
        """
        url = self.source.documentation
        if url:
            import webbrowser as wb

            wb.open_new_tab(url)
        else:
            raise RuntimeError(
                f"No documentation URL given for data source {self.source.id}."
            )

    def clear_cache(self):
        self.cache.clear()

    def series_keys(self, flow_id, use_cache=True):
        """Return all :class:`.SeriesKey` for *flow_id*.

        Returns
        
        list
        """
        # download an empty dataset with all available series keys
        return (
            self.data(flow_id, params={"detail": "serieskeysonly"}, use_cache=use_cache)
            .data[0]
            .series.keys()
        )

    def _make_key(self, resource_type, resource_id, key, dsd):
        """Validate *key* if possible.

        If key is a dict, validate items against the DSD and construct the key
        string which becomes part of the URL. Otherwise, do nothing as key must
        be a str confirming to the REST API spec.
        """
        if not (resource_type == Resource.data and isinstance(key, dict)):
            return key, dsd

        # Select validation method based on agency capabilities
        if dsd:
            # DSD was provided
            pass
        elif self.source.supports[Resource.datastructure]:
            # Retrieve the DataStructureDefinition
            dsd = (
                self.dataflow(
                    resource_id, params=dict(references="all"), use_cache=True
                )
                .dataflow[resource_id]
                .structure
            )

            if dsd.is_external_reference:
                # DataStructureDefinition was not retrieved with the Dataflow
                # query; retrieve it explicitly
                dsd = self.get(resource=dsd, use_cache=True).structure[dsd.id]
        else:
            # Construct a DSD from the keys
            dsd = DataStructureDefinition.from_keys(self.series_keys(resource_id))

        # Make a ContentConstraint from the key
        cc = dsd.make_constraint(key)

        return cc.to_query_string(dsd), dsd

    def _request_from_args(self, kwargs):
        """Validate arguments and prepare pieces for a request."""
        parameters = kwargs.pop("params", {})
        headers = kwargs.pop("headers", {})

        # Resource arguments
        resource = kwargs.pop("resource", None)
        resource_type = kwargs.pop("resource_type", None)
        resource_id = kwargs.pop("resource_id", None)

        try:
            if resource_type:
                resource_type = Resource[resource_type]
        except KeyError:
            raise ValueError(
                f"resource_type ({resource_type!r}) must be in " + Resource.describe()
            )

        # Base URL
        try:
            # base URL specific to resource_type (eg. Bundesbank)?
            base_url = self.source.resource_urls[resource_type]
        except KeyError:
            # fall back to source-wide URL (most sources)
            base_url = self.source.url
        url_parts = [base_url]

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
                    f"mismatch between resource_id={resource_id!r} and "
                    f"resource={resource!r}"
                )
            else:
                resource_id = resource.id

        force = kwargs.pop("force", False)
        if not (force or self.source.supports[resource_type]):
            raise NotImplementedError(
                f"{self.source.id} does not support the"
                f"{resource_type!r} API endpoint; "
                "override using force=True"
            )

        url_parts.append(resource_type.name)

        # Data provider ID to use in the URL
        provider = kwargs.pop("provider", None)
        if resource_type == Resource.data:
            # Requests for data do not specific an agency in the URL
            if provider is not None:
                warn(f"'provider' argument is redundant for {resource_type!r}")
            provider_id = None
        else:
            provider_id = (
                provider
                or getattr(self.source, "api_id", None)
                or getattr(self.source, "id", None)
            )

        url_parts.extend([provider_id, resource_id])

        version = kwargs.pop("version", self.source.default_version)
        if resource_type != Resource.data:
            url_parts.append(version)

        key = kwargs.pop("key", None)
        dsd = kwargs.pop("dsd", None)
        validate = kwargs.pop("validate", True)

        if len(kwargs):
            raise ValueError(f"unrecognized arguments: {kwargs!r}")

        if validate:
            # Make the key, and retain the DSD (if any) for use in parsing
            key, dsd = self._make_key(resource_type, resource_id, key, dsd)
            kwargs["dsd"] = dsd

        url_parts.append(key)

        # Assemble final URL
        url = "/".join(filter(None, url_parts))

        # Parameters: set 'references' to sensible defaults
        if "references" not in parameters:
            if (
                resource_type in [Resource.dataflow, Resource.datastructure]
                and resource_id
            ):
                parameters["references"] = "all"
            elif resource_type == Resource.categoryscheme:
                parameters["references"] = "parentsandsiblings"

        # Headers: use headers from source config if not given by the caller
        if not headers and self.source and resource_type:
            headers = self.source.headers.get(resource_type.name, {})

        return requests.Request("get", url, params=parameters, headers=headers)

    def _request_from_url(self, kwargs):
        url = kwargs.pop("url")
        parameters = kwargs.pop("params", {})
        headers = kwargs.pop("headers", {})

        if len(kwargs):
            raise ValueError(f"unrecognized arguments: {kwargs!r}")

        return requests.Request("get", url, params=parameters, headers=headers)

    def get(
        self,
        resource_type=None,
        resource_id=None,
        tofile=None,
        use_cache=False,
        dry_run=False,
        **kwargs,
    ):
        """Retrieve SDMX data or metadata.

        (Meta)data is retrieved from the :attr:`source` of the current Request.
        The item(s) to retrieve can be specified in one of two ways:

        1. `resource_type`, `resource_id`: These give the type (see
           :class:`Resource`) and, optionally, ID of the item(s). If the
           `resource_id` is not given, all items of the given type are
           retrieved.
        2. a `resource` object, i.e. a :class:`.MaintainableArtefact`:
           `resource_type` and `resource_id` are determined by the object's
           class and :attr:`id <.IdentifiableArtefact.id>` attribute,
           respectively.

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
           :meth:`.CubeRegion.to_query_string` can also be used to create
           properly formatted strings.

        For formats 1 and 2, but not 3, the `key` argument is validated against
        the relevant :class:`.DataStructureDefinition`, either given with the
        `dsd` keyword argument, or retrieved from the web service before the
        main query.

        For the optional `param` keyword argument, some useful parameters are:

        - 'startperiod', 'endperiod': restrict the time range of data to
          retrieve.
        - 'references': control which item(s) related to a metadata resource
          are retrieved, e.g. `references='parentsandsiblings'`.

        Parameters:
        
        resource_type : str or :class:`Resource`, optional
            Type of resource to retrieve.
        resource_id : str, optional
            ID of the resource to retrieve.
        tofile : str or :class:`~os.PathLike` or `file-like object`, 
            or :class:`fsspec.core.OpenFile` with 1 item, optional
            File path or file-like to write SDMX data as it is recieved.
            *file-like* must be binary and writable. It may be used in a with-context 
            (recommended
            when using a fsspec.core.OpenFile.
        use_cache : bool, optional
            If :obj:`True`, return a previously retrieved :class:`~.Message`
            from :attr:`cache`, or update the cache with a newly-retrieved
            Message.
        dry_run : bool, optional
            If :obj:`True`, prepare and return a :class:`requests.Request`
            object, but do not execute the query. The prepared URL and headers
            can be examined by inspecting the returned object.
        **kwargs
            Other, optional parameters (below).

        Other Parameters:
        
        dsd : :class:`~.DataStructureDefinition`
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
            :meth:`~.DataStructureDefinition.make_constraint`.
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
        resource : :class:`~.MaintainableArtefact` subclass
            Object to retrieve. If given, `resource_type` and `resource_id` are
            ignored.
        version : str
            :attr:`~.VersionableArtefact.version>` of a resource to retrieve.
            Default: the keyword 'latest'.

        Returns:
        
        :class:`~.Message` or :class:`~requests.Request`
            The requested SDMX message or, if `dry_run` is :obj:`True`, the
            prepared request object.

        Raises:
        
        NotImplementedError
            If the :attr:`source` does not support the given `resource_type`
            and `force` is not :obj:`True`.

        """
        # Allow sources to modify request args
        # TODO this should occur after most processing, defaults, checking etc.
        #      are performed, so that core code does most of the work.
        if self.source:
            self.source.modify_request_args(kwargs)

        # Handle arguments
        if "url" in kwargs:
            req = self._request_from_url(kwargs)
        else:
            kwargs.update(dict(resource_type=resource_type, resource_id=resource_id))
            req = self._request_from_args(kwargs)

        req = self.session.prepare_request(req)

        # Now get the SDMX message via HTTP
        logger.info("Requesting resource from %s", req.url)
        logger.info("with headers %s" % req.headers)

        # Try to get resource from memory cache if specified
        if use_cache:
            try:
                return self.cache[req.url]
            except KeyError:
                logger.info("Not found in cache")
                pass

        if dry_run:
            return req

        try:
            response = self.session.send(req, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise e from None
        except requests.exceptions.HTTPError as e:
            # Convert a 501 response to a Python NotImplementedError
            if e.response.status_code == 501:
                raise NotImplementedError(
                    "{!r} endpoint at {}".format(resource_type, e.request.url)
                )
            else:
                raise

        # Maybe copy the response to file as it's received
        response_content = remote.ResponseIO(response, tee=tofile)

        # Select reader class
        content_type = response.headers.get("content-type")
        try:
            Reader = get_reader_for_content_type(content_type)
        except ValueError:
            try:
                response, response_content = self.source.handle_response(
                    response, response_content
                )
                content_type = response.headers.get("content-type", None)
                Reader = get_reader_for_content_type(content_type)
            except ValueError:
                raise ValueError(
                    "can't determine a reader for response "
                    "content type: %s" % content_type
                )

        # Instantiate reader
        reader = Reader()

        # Parse the message, using any provided or auto-queried DSD
        msg = reader.read_message(response_content, dsd=kwargs.get("dsd", None))

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
        returns :class:`SeriesKeys <.SeriesKey>` without the corresponding
        :class:`Observations <.Observation>`.

        To count the number of series::

            keys = sdmx.Request('PROVIDER').preview_data('flow')
            len(keys)

        To get a :mod:`pandas` object containing the key values::

            keys_df = sdmx.to_pandas(keys)

        Parameters:
        
        flow_id : str
            Dataflow to preview.
        key : dict, optional
            Mapping of *dimension* to *values*, where *values* may be a
            '+'-delimited list of values. If given, only SeriesKeys that match
            *key* are returned. If not given, preview_data is equivalent to
            ``list(req.series_keys(flow_id))``.

        Returns:
        
        list of :class:`.SeriesKey`
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

    def validate(self, msg, schema_dir=None):
        """
        Validate `msg` against the XML schemas which must
        be installed first. 
        
        Args:
        
        `msg`(pandasdmx.message.Message or file-like):
            the XML message to be validated. If a
            message.Message instance is provided, the file is
            re-downloaded, ideally from cache.
        schema_dir (path-like or str): Optional custom dir where schemas
            are installed. 
            
        Returns True on success.
        
        See also the LXML documentation on the actual validation process.
        """
        # reload message file if Message is provided
        if isinstance(msg, Message):  # and not str
            msg_response = self.session.get(msg.response.url)
            msg = remote.ResponseIO(msg_response)
        # Select reader class
        # Currently, the only reader that can validate
        # sdmx files is the sdmxml reader.
        from .reader.sdmxml import Reader

        # Validate message against the schema referenced in the msg
        return Reader.validate_message(msg, schema_dir=schema_dir)


def read_url(url, **kwargs):
    """Request a URL directly."""
    return Request().get(url=url, **kwargs)


def install_schemas(schema_dir=None, verify=False, **kwargs):
    """
    Download the complete set of XML schemas from `sdmx.org <http://www.sdmx.org>`_. 
    and install them in <schema_dir>. The schemas
    are included in Section 3b of the SDMXML 2.1 standard. Installation
    steps are logged.
    
    Args:
    
    schema_dir (pyth-like or str): defaults to the
        platform-specific appdata dir of the user. As <appname>, "pandasdmx"
        is set.
    verify (bool or path-like): See the 
        `requests` docs on security for details. 
        Default is False to avoid an SSL error.
    **kwargs: optional kwargs passed to
        `requests.get()` to configure the 
        HTTP connection, eg. proxies.
        
    Returns None on success.
    """
    from zipfile import ZipFile

    url = "https://sdmx.org/wp-content/uploads/SDMX_2-1_SECTION_3B_SDMX_ML_Schemas_Samples_2020-07.zip"
    logger.info("Downloading SDMX 2.1 Standard, Section 3b from www.sdmx.org...")
    response = requests.get(url=url, verify=verify, **kwargs)
    content = remote.ResponseIO(response)
    zf = ZipFile(content.tee)
    logger.info("Done.")
    from .reader.sdmxml import Reader
    from pathlib import Path
    import os

    schema_dir = Path(schema_dir or Reader.get_schema_dir())
    logger.info(f"Installing schema files in {str(schema_dir)}")
    for s in zf.infolist():
        if s.filename.startswith("schemas/"):
            fn = s.filename[8:]
            filepath = schema_dir.joinpath(fn)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with zf.open(s, "r") as src:
                with open(filepath, "wb") as target:
                    target.write(src.read())
    logger.info("Done.")
