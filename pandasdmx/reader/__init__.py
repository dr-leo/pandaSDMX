from pathlib import Path

from pandasdmx.reader import sdmxjson as json, sdmxml as xml

#: Reader classes
READERS = [json.Reader, xml.Reader]


def _readers():
    return ", ".join(map(lambda cls: cls.__name__, READERS))


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

    raise ValueError(f"{repr(content)} not recognized by any of {_readers()}")


def get_reader_for_content_type(ctype):
    """Return a reader class for HTTP content type `content`.

    Raises
    ------
    ValueError
        If no reader class matches.

    See also
    --------
    BaseReader.content_types
    """
    for cls in READERS:
        if cls.supports_content_type(ctype):
            return cls

    raise ValueError(f"Content type {repr(ctype)} not supported by any of {_readers()}")


def get_reader_for_path(path):
    """Return a reader class for file `path`.

    Raises
    ------
    ValueError
        If no reader class matches.

    See also
    --------
    BaseReader.suffixes
    """
    suffix = Path(path).suffix
    for cls in READERS:
        if cls.supports_suffix(suffix):
            return cls

    raise ValueError(f"File suffix {repr(suffix)} not supported by any of {_readers()}")


def read_sdmx(filename_or_obj, format=None, **kwargs):
    """
    Load a SDMX-ML or SDMX-JSON message from a file or file-like object.
    A given file-like object is closed after loading.

    Parameters
    ----------
    filename_or_obj : str or :class:`~os.PathLike` 
        or open binary file. A file is not closed explicitly. So it should be passed
        from a with-context.
    format : 'XML' or 'JSON', optional

    Other Parameters
    ----------------
    dsd : :class:`~.DataStructureDefinition`
        For “structure-specific” `format`=``XML`` messages only.
    """
    reader = None

    # pop any dsd from kwargs as these are passed to any FS backend
    kwargs = kwargs.copy()
    dsd = kwargs.pop("dsd", None)

    try:
        # Do we have a path/filename rather than file?
        path = Path(filename_or_obj)

        # Open the file
        obj = open(path, mode="rb", **kwargs)
    except TypeError:
        # Not path-like → opened file
        path = None
        obj = filename_or_obj
        # fsspec.open_files returns a list. So get its only item;
        # multiple files are not allowed.
        if isinstance(obj, list):
            assert len(obj) == 1, ValueError(
                f"Only one file allowed. {len(obj)} passed."
            )
            obj = obj[0]

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

    if dsd:
        return reader().read_message(obj, dsd=dsd)
    else:
        return reader().read_message(obj)
