from pandasdmx.api import Request, open_file
from pandasdmx.source import add_source, list_sources
from pandasdmx.writer import to_pandas
import logging

__all__ = [
    'Request',
    'add_source',
    'list_sources',
    'open_file',
    'to_pandas',
    ]

__version__ = '0.9.0'


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


def odo_register():
    """Enable conversion of .sdmx files with odo (http://odo.readthedocs.org).

    Adds conversion from sdmx to PD.DataFrame to odo graph. Note that native
    discovery of sdmx files is not yet supported. odo will thus convert to
    pd.DataFrame and discover the data shape from there.
    """
    logger.info('Registering with odo...')
    import odo
    from odo.utils import keywords
    import pandas as PD
    from toolz import keyfilter
    import toolz.curried.operator as op

    class PandaSDMX(object):

        def __init__(self, uri):
            self.uri = uri

    @odo.resource.register(r'.*\.sdmx')
    def resource_sdmx(uri, **kwargs):
        return PandaSDMX(uri)

    @odo.discover.register(PandaSDMX)
    def _(sdmx):
        return odo.discover(Request().get(fromfile=sdmx.uri).write())

    @odo.convert.register(PD.DataFrame, PandaSDMX)
    def convert_sdmx(sdmx, **kwargs):
        write = Request().get(fromfile=sdmx.uri).write
        return write(**keyfilter(op.contains(keywords(write)), kwargs))
    logger.info('odo registration complete.')
