import logging

import pandasdmx as sdmx


sdmx.logger.setLevel(logging.INFO)

sdmx.writer.DEFAULT_RTYPE = 'rows'
