import pkg_resources

from pandasdmx.api import Request, read_sdmx, read_url
from pandasdmx.source import add_source, list_sources
from pandasdmx.util import Resource
from pandasdmx.writer import write as to_pandas
import logging

__all__ = [
    'Request',
    'Resource',
    'add_source',
    'list_sources',
    'logger',
    'read_sdmx',
    'read_url',
    'to_pandas',
    ]


try:
    __version__ = pkg_resources.get_distribution('pandasdmx').version
except Exception:
    # Local copy or not installed with setuptools
    __version__ = '999'


#: Top-level logger for pandaSDMX.
logger = logging.getLogger(__name__)


def _init_logger():
    handler = logging.StreamHandler()
    fmt = '{asctime} {name} - {levelname}: {message}'
    handler.setFormatter(logging.Formatter(fmt, style='{'))
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)


_init_logger()
