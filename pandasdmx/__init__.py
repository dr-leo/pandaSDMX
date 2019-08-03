from pandasdmx.api import Request, open_file, read_url
from pandasdmx.source import add_source, list_sources
from pandasdmx.writer import write as to_pandas
import logging

__all__ = [
    'Request',
    'add_source',
    'list_sources',
    'open_file',
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
