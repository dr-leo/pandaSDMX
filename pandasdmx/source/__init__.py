"""SDMX-IM Datasource and related classes."""
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

from pandasdmx.util import BaseModel
from pydantic import validator


sources = {}

endpoints = [
    'categoryscheme',
    'codelist',
    'conceptscheme',
    'data',
    'dataflow',
    'datastructure',
    ]

features = endpoints + ['preview']

DataContentType = Enum('DataContentType', 'XML JSON')


class Source(BaseModel):
    """SDMX-IM RESTDatasource.

    This class describes the location and features supported by an SDMX data
    source. Subclasses can override :meth:`handle_response` and
    :meth:`finish_message` to handle specific types of responses only provided
    by one data source.

    """
    id: str
    url: str
    name: str
    headers: Dict[str, Any] = {}
    data_content_type: DataContentType = DataContentType.XML
    supports: Dict[str, bool] = {}

    @classmethod
    def from_dict(cls, info):
        return cls(**info)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for f in features:
            if f in self.supports:
                continue
            self.supports[f] = (f not in endpoints or
                (self.data_content_type == DataContentType.XML))

    # Hooks
    def handle_response(self, response, content):
        return response, content

    def finish_message(self, message, request, **kwargs):
        return message

    def modify_request_args(self, kwargs):
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
