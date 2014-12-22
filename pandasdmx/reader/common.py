
'''


@author: Dr. Leo
'''

from IPython.utils.traitlets import Unicode
from IPython.config.configurable import LoggingConfigurable


class Reader(LoggingConfigurable):
    
    def __init__(self, agency_id, client, url_factory = None, **kwargs):
        super(Reader, self).__init__(**kwargs)
        self.client = client
        self.agency_id = agency_id
        self.url_factory = url_factory or URLFactory()
    
    def get_source(self, *args, from_file = None, to_file = None, **kwargs):
        # Construct the URL and get source file
        url_suffix = self.url_factory.url_suffix(*args, **kwargs)
        self.source = self.client.get(url_suffix, from_file = from_file)
        if to_file:
            with open(to_file, 'wb') as dest:
                dest.write(self.source.read())
                self.source.seek(0)
    
class URLFactory:
    
    def url_suffix(self, resource_name, flowref, key = u'', startperiod = None, endperiod = None):
        parts = [resource_name, flowref]
        if key: parts.append(key)
        query_url = '/'.join(parts)
        if startperiod: 
            query_url += '?startperiod={0}'.format(startperiod)
            if endperiod: query_url += '&endperiod={0}'.format(endperiod)
        elif endperiod: query_url += '?endperiod={0}'.format(endperiod) 
        return query_url
    

    
    