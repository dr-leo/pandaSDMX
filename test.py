!#('http://data.fao.org/sdmx',
                     '2_1','FAO')

from sdmx import client

ecb = client('ECB')
flows = ecb.dataflows())