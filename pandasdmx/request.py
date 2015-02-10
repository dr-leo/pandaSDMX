# encoding: utf-8

'''
.. module:: pandasdmx.agency
    
     
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; forked from http://github.com/widukind/pysdmx
'''



from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Instance
from pandasdmx.remote import REST
from pandasdmx.utils import str_type 
from pandasdmx.reader.sdmxml import SDMXMLReader 


__all__ = ['Request']


class Request(LoggingConfigurable):
    """
    Request SDMX data and metadata from remote or local sources.
    """
   

    client = Instance(REST, config = True, help = """
    REST or similar client to communicate with the web service""")
    
    _agencies = {
        'ESTAT' : {
            'name' : 'Eurostat',
            'url' : 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'},
        'ECB' : {
            'name' : 'European Central Bank',
            'url' : 'http://sdw-wsrest.ecb.int/service'}
            }
    _resources = ['dataflow', 'datastructure', 'data', 'category', 'constraint']
                    
    def __init__(self, agency = ''):
        super(Request, self).__init__()
        self.client = REST()
        if not agency or agency in self._agencies:
            self.agency = agency
        else:
            raise ValueError('If given, agency must be one of {0}'.format(
                            list(self._agencies)))
        

    def get_reader(self):
        return SDMXMLReader(self)
    
    
    def get(self, agency = '', resource = '', flow = '', key = '', params = {},
                 from_file = None, to_file = None):
        '''
        Load a source file identified by the URL suffix or filename given as from_file kwarg.
        If to_file is not None, save the file under that name.
        return a reader for the file as stored by self.client (mostly in a Spooled TempFile, or, if
        the downloaded file has been saved to a permanent local file, for that file.
        '''
        # Validate args
        if ((agency and agency not in self._agencies)
        or (not agency and not self.agency)):
            raise ValueError('agency must be one of {0}'.format(
                            list(self._agencies)))
        self.agency = agency
        if not agency and not from_file:
            raise ValueError('Either agency or from_file must be set.')    
        # 'Validate resource
        if resource and resource not in self._resources:
            raise ValueError('resource must be one of {0}'.format(self._resources))
        # flow: if it is not a str or unicode type, 
        # but, e.g., a model.DataflowDefinition, 
        # extract its ID
        if not isinstance(flow, (str_type, str)):
            flow = flow.id
            
        # Construct URL from the given non-empty substrings.
        # Remove None's and '' first. Then join them to form the base URL.
        # Any parameters are appended by remote module.
        if agency: 
            parts = filter(None, [self._agencies[agency]['url'], 
                              agency, resource, flow, key])
            base_url = '/'.join(parts)
        else: base_url = '' # in which case from_file must be True
        
        # Now get the SDMX message either via http or as local file 
        source = self.client.get(base_url, params = params, from_file = from_file)
        if to_file:
            with open(to_file, 'wb') as dest:
                dest.write(source.read())
                source.seek(0)
        return self.get_reader().initialize(source)           