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
    'read_sdmx',
    'read_url',
    'to_pandas',
    ]

__version__ = '1.0.0-dev'


def _init_logger():
    logger = logging.getLogger('pandasdmx')
    handler = logging.StreamHandler()
    fmt = logging.Formatter(
        '%(asctime)s %(name)s - %(levelname)s: %(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    return logger


logger = _init_logger()
