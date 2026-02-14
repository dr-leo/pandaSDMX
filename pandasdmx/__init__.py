"""Statistical Data and Metadata eXchange (SDMX) for the Python data ecosystem"""


from pandasdmx.api import Request, read_url, install_schemas
from pandasdmx.reader import read_sdmx
from pandasdmx.source import add_source, list_sources
from pandasdmx.util import Resource
from pandasdmx.writer import to_pandas, to_xml
import logging

__all__ = [
    "Request",
    "Resource",
    "add_source",
    "list_sources",
    "logger",
    "read_sdmx",
    "read_url",
    "to_pandas",
    "to_xml",
]

__version__ = "1.10.2"


#: Top-level logger.
logger = logging.getLogger(__name__)


def _init_logger():
    handler = logging.StreamHandler()
    fmt = "{asctime} {name} - {levelname}: {message}"
    handler.setFormatter(logging.Formatter(fmt, style="{"))
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)


_init_logger()
