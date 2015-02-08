# encoding: utf-8

'''
.. module:: pandasdmx.agency
    
     
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; forked from http://github.com/widukind/pysdmx
'''



from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Instance
from pandasdmx.remote import REST 
from pandasdmx.reader.sdmxml import SDMXMLReader 


__all__ = ['Request']


class Request(LoggingConfigurable):
    """
    Request SDMX data and metadata from remote or local sources.
    """
   

    client = Instance(REST, config = True, help = """
    REST or similar client to communicate with the web service""")
    
    agencies = {
        'ESTAT' : {
            'name' : 'Eurostat',
            'url' : 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'},
        'ECB' : {
            'name' : 'European Central Bank',
            'url' : 'http://sdw-wsrest.ecb.int/service'}
            }
                    
    def __init__(self, agency):
        # Validate args
        if agency not in self.agencies:
            raise ValueError('agency must be one of {0}'.format(list(self.agencies)))
        self.agency_id = agency
        self.client = REST(self.agencies[agency]['url'])
        

    def get_reader(self):
        return SDMXMLReader(self)
    
    
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
        # First, we handle the case that flowref is an
        # IdentifiableArtefact. If so, we take the id string as dataflow id.
        try:
            flowref = flowref.id
        except AttributeError: pass
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
            

        
class QueryFactory:
    
    def url_suffix(self, resource_name, flowref, key = u'', startperiod = None, endperiod = None):
        parts = [resource_name, flowref]
        if key: parts.append(key)
        query_url = '/'.join(parts)
        if startperiod: 
            query_url += '?startperiod={0}'.format(startperiod)
            if endperiod: query_url += '&endperiod={0}'.format(endperiod)
        elif endperiod: query_url += '?endperiod={0}'.format(endperiod) 
        return query_url
    
    