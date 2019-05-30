from enum import Enum
from importlib import import_module
from io import TextIOWrapper
import json
from typing import (
    Any,
    Dict,
    Union,
    )

from pkg_resources import resource_stream

from pandasdmx.util import BaseModel, Resource
from pydantic import validator


sources = {}

DataContentType = Enum('DataContentType', 'XML JSON')


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
    #: Base URL for queries
    url: str
    #: Human-readable name of the data source
    name: str
    headers: Dict[str, Any] = {}
    #: :class:`pandasdmx.util.DataContentType` indicating the type of data
    #: returned by the source.
    data_content_type: DataContentType = DataContentType.XML
    #: Mapping from :class:`Resource <pandasdmx.util.Resource>` to
    #: :class:`bool` indicating support for SDMX REST API features. Two
    #: additional keys are valid:
    #:
    #: - ``'preview'=True`` if the source supports ``?detail=serieskeysonly``.
    #:   See :meth:`preview_data <pandasdmx.Request.preview_data>`.
    #: - ``'structure-specific data'=True`` if the source can return structure-
    #:   specific data messages.
    supports: Dict[Union[str, Resource], bool] = {}

    @classmethod
    def from_dict(cls, info):
        return cls(**info)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set default supported features
        for feature in list(Resource) + ['preview', 'structure-specific data']:
            self.supports.setdefault(
                feature, self.data_content_type == DataContentType.XML)

    # Hooks
    def handle_response(self, response, content):
        """Handle response content of unknown type.

        This hook is called by :meth:`pandasdmx.Request.get` *only* when
        the `content` cannot be parsed as XML or JSON.

        See :meth:`ESTAT <pandasdmx.source.estat.Source.handle_response>` and
        :meth:`SGR <pandasdmx.source.sgr.Source.handle_response>` for example
        implementations.
        """
        return response, content

    def finish_message(self, message, request, **kwargs):
        """Postprocess retrieved message.

        This hook is called by :meth:`pandasdmx.Request.get` after a
        :class:`pandasdmx.message.Message` object has been successfully
        parsed from the query response.

        See :meth:`ESTAT <pandasdmx.source.estat.Source.finish_message>` for an
        example implementation.
        """
        return message

    def modify_request_args(self, kwargs):
        """Modify arguments used to build query URL.

        This hook is called by :meth:`pandasdmx.Request.get` to modify the
        keyword arguments before the query URL is built.

        See :meth:`SGR <pandasdmx.source.sgr.Source.modify_request_args>` for
        an example implementation.
        """
        pass

    @validator('id')
    def _validate_id(cls, value):
        assert getattr(cls, '_id', value) == value
        return value

    @validator('data_content_type', pre=True)
    def _validate_dct(cls, value):
        if isinstance(value, DataContentType):
            return value
        else:
            return DataContentType[value]


class _NoSource(Source):
    id = ''
    url = ''
    name = ''


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

    id = info['id'] if id is None else id

    info.update(kwargs)

    if id in sources:
        raise ValueError("Data source '%s' already defined; use override=True",
                         id)

    # Maybe import a subclass that defines a hook
    SourceClass = Source
    try:
        mod = import_module('.' + id.lower(), 'pandasdmx.source')
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
    with resource_stream('pandasdmx', 'sources.json') as f:
        # TextIOWrapper is for Python 3.5 compatibility
        for info in json.load(TextIOWrapper(f)):
            add_source(info)


load_package_sources()
