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
from importlib import import_module

__all__ = ['Request']


class Request(LoggingConfigurable):
    """
    Request SDMX data and metadata from remote or local sources.
    """
   

    client = Instance(REST, config = True, help = """
    REST or similar client to communicate with the web service""")
    
    _agencies = {
        '' : None, # empty agency for convenience when from_file is given.
        'ESTAT' : {
            'name' : 'Eurostat',
            'url' : 'http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest'},
        'ECB' : {
            'name' : 'European Central Bank',
            'url' : 'http://sdw-wsrest.ecb.int/service'},
        'ILO' : {
            'name' : 'International Labor Organisation',
            'url' : 'http://www.ilo.org/ilostat/sdmx/ws/rest'}
            }
    _resources = ['dataflow', 'datastructure', 'data', 'categoryscheme', 
                  'categorisation', 'codelist', 'conceptscheme']
                    
    def __init__(self, agency = '',
                 writer = {'name': 'pandasdmx.writer.data2pandas'}):
        super(Request, self).__init__()
        self.client = REST()
        self.agency = agency
        self.writer = writer
        

    def get_reader(self):
        return SDMXMLReader(self)
    
    
    @property
    def agency(self):
        return self._agency
    @agency.setter
    def agency(self, value):
        if value in self._agencies:
            self._agency = value
        else:
            raise ValueError('If given, agency must be one of {0}'.format(
                            list(self._agencies)))
            
    
    def get(self, resource_type = '', resource_id = '', agency = '', key = '', params = {},
                 from_file = None, to_file = None):
        '''
        Load a source file identified by the URL suffix or filename given as from_file kwarg.
        If to_file is not None, save the file under that name.
        return a reader for the file as stored by self.client (mostly in a Spooled TempFile, or, if
        the downloaded file has been saved to a permanent local file, for that file.
        '''
        # Validate args
        if not agency: agency = self.agency 
        # Validate resource if no filename is specified
        if not from_file and resource_type not in self._resources:
            raise ValueError('resource must be one of {0}'.format(self._resources))
        # resource_id: if it is not a str or unicode type, 
        # but, e.g., a model.DataflowDefinition, 
        # extract its ID
        if resource_id and not isinstance(resource_id, (str_type, str)):
            resource_id = resource_id.id
            
        # Construct URL from the given non-empty substrings.
        # if data is requested, omit the agency part. See the query examples
        # from Eurostat. Hopefully ECB excepts this.
        if resource_type in ['data', 'categoryscheme']: agency = ''
        # Remove None's and '' first. Then join them to form the base URL.
        # Any parameters are appended by remote module.
        if self.agency: 
            parts = [self._agencies[self.agency]['url'], 
                            resource_type, agency, resource_id, key]
            base_url = '/'.join(filter(None, parts))
            
            # Set references to sensible defaults  
            if 'references' not in params:
                if resource_type == 'dataflow' and resource_id: pass 
                # params['references'] = 'all'
                elif resource_type == 'categoryscheme':
                    params['references'] = 'parentsandsiblings'
                    
        elif from_file: 
            base_url = ''
        else:
            raise ValueError('Either agency or from_file must be given.') 
        
        # Now get the SDMX message either via http or as local file 
        source, url = self.client.get(base_url, params = params, from_file = from_file)
        if to_file:
            with open(to_file, 'wb') as dest:
                dest.write(source.read())
                source.seek(0)
        msg = self.get_reader().initialize(source)
        return Response(msg, url, writer = self.writer)
    
    
class Response:
    def __init__(self, msg, url, writer = None):
        self.msg =msg
        self.url = url
        # Initialize the writer if given
        if writer:
            writer_module = import_module(writer['name'])
            writer_cls = writer_module.Writer
            self._writer = writer_cls(self.msg)
            
    def write(self, *args, **kwargs): 
        return self._writer.write(*args, **kwargs)
            
        
        
        