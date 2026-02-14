try:
    from pydantic.v1 import HttpUrl
except Exception:
    from pydantic import HttpUrl
from enum import Enum
from importlib import import_module, resources
import json
from typing import Any, Dict, Union, Optional

from pandasdmx.model import DataStructureDefinition
from pandasdmx.util import BaseModel, Resource, validator


sources: Dict[str, "Source"] = {}

DataContentType = Enum("DataContentType", "XML JSON")


class Source(BaseModel):
    """SDMX-IM RESTDatasource.

    This class describes the location and features supported by an SDMX data
    source. Subclasses may override the hooks in order to handle specific
    features of different REST web services:

    .. autosummary::
       handle_response
       finish_message
       modify_request_args

    """

    #: ID of the data source
    id: str
    #: Optional API IDTakes precedence over id when URL is constructed
    # Useful if a provider offers several APIs
    api_id: Optional[str]

    #: Base URL for queries
    url: Optional[HttpUrl]

    #: Human-readable name of the data source
    name: str

    #: documentation URL of the data source
    documentation: Optional[HttpUrl]

    headers: Dict[str, Any] = {}

    # resource-specific URLs for end-point. Overrides `url` param
    resource_urls: Dict[str, HttpUrl] = {}

    default_version: str = "latest"

    #: :class:`.DataContentType` indicating the type of data returned by the
    #: source.
    data_content_type: DataContentType = DataContentType.XML

    #: Mapping from :class:`~sdmx.Resource` to :class:`bool` indicating support
    #: for SDMX REST API features. Two additional keys are valid:
    #:
    #: - ``'preview'=True`` if the source supports ``?detail=serieskeysonly``.
    #:   See :meth:`.preview_data`.
    #: - ``'structure-specific data'=True`` if the source can return structure-
    #:   specific data messages.
    supports: Dict[Union[str, Resource], bool] = {Resource.data: True}

    @classmethod
    def from_dict(cls, info):
        return cls(**info)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set default supported features
        for feature in list(Resource) + ["preview", "structure-specific data"]:
            self.supports.setdefault(
                feature, self.data_content_type == DataContentType.XML
            )

    # Hooks
    def handle_response(self, response, content):
        """Handle response content of unknown type.

        This hook is called by :meth:`.Request.get` *only* when
        the `content` cannot be parsed as XML or JSON.

        See :meth:`.estat.Source.handle_response` and
        :meth:`.sgr.Source.handle_response` for example implementations.
        """
        return response, content

    def finish_message(self, message, request, **kwargs):
        """Postprocess retrieved message.

        This hook is called by :meth:`.Request.get` after a :class:`.Message`
        object has been successfully parsed from the query response.

        See :meth:`.estat.Source.finish_message` for an example implementation.
        """
        return message

    def modify_request_args(self, kwargs):
        """Modify arguments used to build query URL.

        This hook is called by :meth:`.Request.get` to modify the keyword
        arguments before the query URL is built.

        The default implementation handles requests for 'structure-specific
        data' by adding an HTTP 'Accepts:' header when a 'dsd' is supplied as
        one of the `kwargs`.

        See :meth:`.sgr.Source.modify_request_args` for an example override.

        Returns
        -------
        None
        """
        if self.data_content_type is DataContentType.XML:
            dsd = kwargs.get("dsd", None)
            if isinstance(dsd, DataStructureDefinition):
                kwargs.setdefault("headers", {})
                kwargs["headers"].setdefault(
                    "Accept",
                    "application/vnd.sdmx.structurespecificdata+xml;" "version=2.1",
                )

    @validator("id")
    def _validate_id(cls, value):
        assert getattr(cls, "_id", value) == value
        return value

    @validator("data_content_type", pre=True)
    def _validate_dct(cls, value):
        if isinstance(value, DataContentType):
            return value
        else:
            return DataContentType[value]


class _NoSource(Source):
    def __init__(self):
        super().__init__(id="", url=None, name="", documentation=None)


NoSource = _NoSource()


def add_source(info, id=None, override=False, **kwargs):
    """Add a new data source.

    The *info* expected is in JSON format:

    .. code-block:: json

        {
          "id": "ESTAT",
          "documentation": "http://data.un.org/Host.aspx?Content=API",
          "url": "http://ec.europa.eu/eurostat/SDMX/diss-web/rest",
          "name": "Eurostat",
          "supported": {"codelist": false, "preview": true}
        }

    …with unspecified values using the defaults; see
    :class:`Source`.

    Parameters
    ----------
    info : dict-like
        String containing JSON information about a data source.
    id : str
        Identifier for the new datasource. If :obj:`None` (default), then
        `info['id']` is used.
    override : bool
        If :obj:`True`, replace any existing data source with *id*.
        Otherwise, raise :class:`ValueError`.
    **kwargs
        Optional callbacks for *handle_response* and *finish_message* hooks.

    """
    if isinstance(info, str):
        info = json.loads(info)

    id = info["id"] if id is None else id

    info.update(kwargs)

    if id in sources and not override:
        raise ValueError(f"Data source '{id}' already defined; use override=True")

    # Maybe import a subclass that defines a hook
    SourceClass = Source
    try:
        mod = import_module("." + id.lower(), "pandasdmx.source")
    except ImportError:
        pass
    else:
        SourceClass = mod.Source

    sources[id] = SourceClass.from_dict(info)


def list_sources():
    """Return a sorted list of valid source IDs.

    These can be used to create :class:`Request` instances.
    """
    return sorted(sources.keys())


def load_package_sources():
    """Discover all sources listed in ``sources.json``."""
    with resources.files("pandasdmx").joinpath("sources.json").open("rb") as f:
        for info in json.load(f):
            add_source(info)


load_package_sources()
