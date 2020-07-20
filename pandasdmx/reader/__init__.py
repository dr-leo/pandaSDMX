from pathlib import Path
from typing import List, Mapping, Type

from . import sdmxjson, sdmxml


#: Reader classes
READERS: List[Type] = []

#: Mapping from HTTP content type to reader class.
CTYPE_READER: Mapping[str, Type] = {}

#: Mapping from file path suffix to reader class.
SUFFIX_READER: Mapping[str, Type] = {}


def detect_content_reader(content):
    """Return a reader class for `content`.

    The :meth:`.BaseReader.detect` method for each class in :data:`READERS` is called;
    if a reader signals that it is compatible with `content`, then that class is
    returned.

    Raises
    ------
    ValueError
        If no reader class matches.
    """
    for cls in READERS:
        if cls.detect(content):
            return cls

    raise ValueError(f"{repr(content)} not recognized by any of {READERS}")


def get_reader_for_content_type(ctype):
    """Return a reader class for HTTP content type `content`.

    Raises
    ------
    ValueError
        If no reader class matches.

    See also
    --------
    CTYPE_READER
    """
    # Split off e.g. "; version=2.1"
    ctype = str(ctype).split(";")[0].strip()

    try:
        return CTYPE_READER[ctype]
    except KeyError:
        raise ValueError(f"Unsupported content type: {ctype}") from None


def get_reader_for_path(path):
    """Return a reader class for file `path`.

    Raises
    ------
    ValueError
        If no reader class matches.

    See also
    --------
    SUFFIX_READER
    """
    try:
        return SUFFIX_READER[path.suffix.lower()]
    except KeyError:
        raise ValueError(f"Unsupported file suffix: {path.suffix}") from None


def register(reader_cls):
    """Register `reader_cls`."""
    global READERS, CTYPE_READER, SUFFIX_READER

    READERS.append(reader_cls)

    for ctype in reader_cls.content_types:
        CTYPE_READER[ctype] = reader_cls

    for suffix in reader_cls.suffixes:
        SUFFIX_READER[suffix] = reader_cls


# Register built-in readers
register(sdmxjson.Reader)
register(sdmxml.Reader)


def read_sdmx(filename_or_obj, format=None, **kwargs):
    """Load a SDMX-ML or SDMX-JSON message from a file or file-like object.

    Parameters
    ----------
    filename_or_obj : str or :class:`~os.PathLike` or file
    format : 'XML' or 'JSON', optional

    Other Parameters
    ----------------
    dsd : :class:`~.DataStructureDefinition`
        For “structure-specific” `format`=``XML`` messages only.
    """
    reader = None

    try:
        path = Path(filename_or_obj)

        # Open the file
        obj = open(path, "rb")
    except TypeError:
        # Not path-like → opened file
        path = None
        obj = filename_or_obj

    if path:
        try:
            # Use the file extension to guess the reader
            reader = get_reader_for_path(path)
        except ValueError:
            pass

    if not reader:
        try:
            reader = get_reader_for_path(Path(f"dummy.{format.lower()}"))
        except (AttributeError, ValueError):
            pass

    if not reader:
        # Read a line and then return the cursor to the initial position
        pos = obj.tell()
        first_line = obj.readline().strip()
        obj.seek(pos)

        try:
            reader = detect_content_reader(first_line)
        except ValueError:
            pass

    if not reader:
        raise RuntimeError(
            f"cannot infer SDMX message format from path {repr(path)}, "
            f"format={format}, or content '{first_line[:5].decode()}..'"
        )

    return reader().read_message(obj, **kwargs)
