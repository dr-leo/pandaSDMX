# encoding: utf-8

'''
.. module:: pandasdmx.agency
    
     
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; forked from http://github.com/widukind/pysdmx
'''



from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Instance, Unicode
from pandasdmx.remote import REST, QueryFactory
from pandasdmx.reader.sdmxml import SDMXMLReader 


__all__ = ['ECB', 'Eurostat']


class Agency(LoggingConfigurable):
    """
    Base class for agencies. Contains data on the web service.
    """
   

    client = Instance(REST, config = True, help = """
    REST or similar client to communicate with the web service""")
    base_url = Unicode(config = True, help = 'Base URL of the REST service')
    reader = Instance('pandasdmx.reader.common.Reader', config = True, help = 
    ''
        """class path to the Reader subclass""")

    def get(self, url_suffix = u'', from_file = None, to_file = None, **kwargs):
        '''
        Load a source file identified by the URL suffix or filename.
        If to_file is not None, save the file under that name.
        return the downloaded file as stored by self.client (mostly in a Spooled TempFile, or, if
        the downloaded file has been saved to a permanent local file, return that file.
        '''
         
        source = self.client.get(url_suffix, from_file = from_file)
        if to_file:
            with open(to_file, 'wb') as dest:
                dest.write(source.read())
                source.seek(0)
        return source  
         

class ECB(Agency):
    """
    European Central Bank
    """
    base_url = Unicode('http://sdw-wsrest.ecb.int/service', config = True, help = 'Base URL of the REST service')

    def __init__(self):
        super(ECB, self).__init__()
        self.agency_id = 'ECB'
        self.query = QueryFactory()
        self.client = REST(self.base_url)
        self.reader = SDMXMLReader(self.agency_id, self.client)
    
    
    def resource(self, make_url_suffix):
        def f(self, *args, to_file = None, **kwargs):
            url_suffix = make_url_suffix(*args, **kwargs)
            source = self.get(url_suffix = url_suffix, to_file = to_file)
            return self.reader.parse(source)
        return f
    
    @resource                
    def dataflows(self, to_file = None):
        return '/'.join(['dataflow', self.agency_id, 'all', 'latest'])
        
    @resource
    def datastructure(self, flowref):
        return '/'.join(['datastructure', self.agency_id, 'DSD_' + flowref])
    
    @resource
    def categories(self):
        return 'categories'
    
            
        
class Eurostat(ECB):
    """
    Statistical office of the European Union
    """

    base_url = 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'
    agency_id = 'ESTAT'
    
    