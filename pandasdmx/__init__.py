# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
pandaSDMX - a Python package for SDMX - Statistical Data and Metadata eXchange

'''


from pandasdmx.api import Request
import logging

__all__ = ['Request']

__version__ = '0.4a1'


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


def odo_support():
    # Register with odo if available
    try:
        import odo

        @odo.resource.register('.*\.sdmx')
        def resource_sdmx(uri, **kwargs):
            return Request().get(fromfile=uri).write()
        logger.info("Registered '*.sdmx' with odo.")
    except:
        logger.info('Could not register with odo.')

odo_support()
