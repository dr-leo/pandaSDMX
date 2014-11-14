# encoding: utf-8

'''
.. module:: pandasdmx.agency
    
    :synopsis: A Python- and pandas-powered client for statistical data and metadata exchange 
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; forked from http://github.com/widukind/pysdmx
'''
# uncomment this for debugging and use embed() to invoke an ipython shell
# from IPython import embed

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Instance
from pandasdmx import resource, client 



# # Descriptors for some data providers. Pass values to client() 
# providers = {
#     'Eurostat' : ('http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest',
#                     '2_1','ESTAT'),
#     'ECB' : ('http://sdw-wsrest.ecb.int/service',
#                      '2_1','ECB'),
#     'ILO' : ('http://www.ilo.org/ilostat/sdmx/ws/rest/',
#                             '2_1','ILO'),
#     'FAO' : ('http://data.fao.org/sdmx',
#                      '2_1','FAO')
#     }    


class Agency(Configurable):
    """
    Base class for agencies. Contains data on the web service.
    """
   

    client = Instance('pandasdmx.client.BaseClient', config = True, help = """
    client to communicate with the web service""")
    data = Instance('pandasdmx.resource.Data21', config = True, help = 
        """class path of the data resource""")
    
 

    
    
    def __init__(self):
        super(Agency, self).__init__()

class ECB(Agency):
    """
    European Central Bank
    """

    url = 'http://sdw-wsrest.ecb.int/service'
    id = 'ECB'
    
    def __init__(self):
        super(ECB, self).__init__()


class Eurostat(Agency):
    """
    Statistical office of the European Union
    """

    url = 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'
    id = 'ESTAT'
    
    def __init__(self):
        super(Eurostat, self).__init__()


        
