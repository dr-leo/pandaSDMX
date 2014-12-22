# encoding: utf-8

'''
.. module:: pandasdmx.agency
    
     
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; forked from http://github.com/widukind/pysdmx
'''



from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Instance, Unicode
from pandasdmx import client
from pandasdmx.reader.sdmxml import SDMXMLReader 


__all__ = ['ECB', 'Eurostat']


class Agency(LoggingConfigurable):
    """
    Base class for agencies. Contains data on the web service.
    """
   

    client = Instance(client.REST, config = True, help = """
    REST or similar client to communicate with the web service""")
    reader = Instance('pandasdmx.reader.common.Reader', config = True, help = 
        """class path to the Reader subclass""")
    
 

    
    
    def __init__(self):
        super(Agency, self).__init__()

class ECB(Agency):
    """
    European Central Bank
    """

    base_url = Unicode('http://sdw-wsrest.ecb.int/service')
    agency_id = Unicode('ECB')
    client = Instance(client.REST, config=True, help='client class e.g. for REST access')
    
    def __init__(self):
        super(ECB, self).__init__()
        self.client = client.REST(self.base_url)
        
        
class Eurostat(ECB):
    """
    Statistical office of the European Union
    """

    base_url = 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'
    agency_id = 'ESTAT'
    
    def __init__(self):
        super(Eurostat, self).__init__()


        
