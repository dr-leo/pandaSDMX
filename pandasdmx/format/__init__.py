from collections import namedtuple
from enum import IntFlag

#: Structure of elements in :data:`FORMATS`.
Format = namedtuple("Format", "mime base data meta extra")

#: Values for the ``extra`` field of :class:`Format`.
Extra = IntFlag("Extra", "ss ts")

#: SDMX formats. Each record is an instance of :class:`Format`, containing the following
#: fields:
#:
#: - ``mime``: the complete MIME type for the format.
#: - ``base``: the base MIME type or file format: one of "xml", "json", or "csv".
#: - ``data``: :obj:`True` if this format contains (meta)data; :obj:`False` if it
#:   contains (meta)data structures.
#: - ``meta``: :obj:`True` if this format contains metadata (or metadata structures);
#:   :obj:`False` otherwise.
#: - ``extra``: an instance of :class:`Extra`. Zero or more of:
#:
#:   - ``ss``: for structure-specific (meta)data.
#:   - ``ts``: for time-series data.
FORMATS = [
    Format("application/vnd.sdmx.genericdata+xml;version=2.1", "xml", True, False, 0),
    Format(
        "application/vnd.sdmx.structurespecificdata+xml;version=2.1",
        "xml",
        True,
        False,
        Extra.ss,
    ),
    Format(
        "application/vnd.sdmx.generictimeseriesdata+xml;version=2.1",
        "xml",
        True,
        False,
        Extra.ts,
    ),
    Format(
        "application/vnd.sdmx.structurespecifictimeseriesdata+xml;version=2.1",
        "xml",
        True,
        False,
        Extra.ss | Extra.ts,
    ),
    Format("application/vnd.sdmx.data+json;version=1.0.0", "json", True, False, 0),
    Format("application/vnd.sdmx.data+csv;version=1.0.0", "csv", True, False, 0),
    Format("application/vnd.sdmx.structure+xml;version=2.1", "xml", False, False, 0),
    Format(
        "application/vnd.sdmx.structure+json;version=1.0.0", "json", False, False, 0
    ),
    Format("application/vnd.sdmx.schema+xml;version=2.1", "xml", False, True, 0),
    Format(
        "application/vnd.sdmx.genericmetadata+xml;version=2.1", "xml", True, True, 0
    ),
    Format(
        "application/vnd.sdmx.structurespecificmetadata+xml;version=2.1",
        "xml",
        True,
        True,
        Extra.ss,
    ),
]


def list_content_types(**filters):
    """Return ``mime`` for each format in :data:`FORMATS` matching `filters`."""
    result = []
    for format in FORMATS:
        if not all(getattr(format, field) == value for field, value in filters.items()):
            continue
        result.append(format.mime)
    return result
