"""SDMX-IM Datasource and related classes."""
from importlib import import_module
import json

from pkg_resources import resource_stream
from traitlets import CaselessStrEnum, Dict, HasTraits, Unicode


sources = {}

endpoints = [
    'categoryscheme',
    'codelist',
    'conceptscheme',
    'data',
    'dataflow',
    'datastructure',
    ]


class Source(HasTraits):
    """SDMX-IM Datasource.

    This class describes the location and features supported by an SDMX
    endpoint. Subclasses can override :meth:`handle_response` to handle
    specific types of responses only provided by one endpoint.

    This class roughly conforms to the SDMX-IM RESTDatasource.
    """
    id = Unicode()
    url = Unicode()
    name = Unicode()
    headers = Dict()
    data_content_type = CaselessStrEnum('XML JSON'.split(),
                                        default_value='XML')
    supports = Dict(default_value={ep: True for ep in endpoints})

    @classmethod
    def from_dict(cls, info):
        unsupported = info.pop('unsupported', [])
        info['supports'] = {ep: ep not in unsupported for ep in endpoints}
        return cls(**info)

    def __init__(self, **kwargs):
        assert getattr(self, '_id', kwargs['id']) == kwargs['id']
        super(Source, self).__init__(**kwargs)

    # Hooks
    def handle_response(self, response, content):
        return response, content

    def finish_message(self, message, request, **kwargs):
        return message


def add_source(info, id=None, override=False):
    """Add a new datasource.

    *info* is a dict-like, or a string containing JSON information, about a
    data source. *id* is the short ID string of the data source; if `None`
    (default), then `info['id']` is used.

    Adding a datasource with an existing *id* raises `ValueError`, unless
    *override* is `True` (default: `False`).
    """
    if isinstance(info, str):
        info = json.loads(info)

    id = info['id'] if id is None else id

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
    """Return a sorted list of valid agency IDs.

    These can be used to create Request instances.
    """
    return sorted(sources.keys())


def load_package_sources():
    """Discover all sources listed in agencies.json."""
    with resource_stream('pandasdmx', 'agencies.json') as f:
        for id, info in json.load(f).items():
            add_source(info, id)


load_package_sources()
