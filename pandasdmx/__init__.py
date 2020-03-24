from setuptools_scm import get_version

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

__version__ = get_version(root='..', relative_to=__file__)


#: Top-level logger for pandaSDMX.
logger = logging.getLogger(__name__)


def _init_logger():
    handler = logging.StreamHandler()
    fmt = '{asctime} {name} - {levelname}: {message}'
    handler.setFormatter(logging.Formatter(fmt, style='{'))
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)


_init_logger()
