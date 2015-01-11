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
    base_url = Unicode


    def get_reader(self):
        return SDMXMLReader(self.agency_id, self.client)
    
    
    def get(self, url_suffix = u'', from_file = None, to_file = None, **kwargs):
        '''
        Load a source file identified by the URL suffix or filename given as from_file kwarg.
        If to_file is not None, save the file under that name.
        return a reader for the file as stored by self.client (mostly in a Spooled TempFile, or, if
        the downloaded file has been saved to a permanent local file, for that file.
        '''
         
        source = self.client.get(url_suffix = url_suffix, from_file = from_file)
        if to_file:
            with open(to_file, 'wb') as dest:
                dest.write(source.read())
                source.seek(0)
        return self.get_reader().initialize(source)  
         
    def dataflows(self, **kwargs):
        url_suffix = '/'.join(['dataflow', self.agency_id, 'all', 'latest'])
        return self.get(url_suffix = url_suffix, **kwargs)
    
    def datastructure(self, flowref, **kwargs):
        url_suffix = '/'.join(['datastructure', self.agency_id, 'DSD_' + flowref])
        return self.get(url_suffix = url_suffix, **kwargs)
    
    def data(self, flowref, key = '', startperiod = None, endperiod = None, **kwargs):
        parts = [self.resource_name, flowref]
        if key: parts.append(key)
        url_suffix = '/'.join(parts)
        if startperiod: 
            url_suffix += '?startperiod={0}'.format(startperiod)
            if endperiod: url_suffix += '&endperiod={0}'.format(endperiod)
        elif endperiod: url_suffix += '?endperiod={0}'.format(endperiod) 
        return self.get(url_suffix = url_suffix, **kwargs)

    def categories(self, **kwargs):
        return self.get(url_suffix = 'category', **kwargs)
            

class ECB(Agency):
    """
    European Central Bank
    """
    

    def __init__(self):
        super(ECB, self).__init__()
        self.base_url = 'http://sdw-wsrest.ecb.int/service'
        self.agency_id = 'ECB'
        self.client = REST(self.base_url)
         
                    
        
class Eurostat(Agency):
    """
    Statistical office of the European Union
    """

    def __init__(self):
        super(Eurostat, self).__init__()
        self.base_url = 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'
        self.agency_id = 'ESTAT'
        self.client = REST(self.base_url)
        
    
    