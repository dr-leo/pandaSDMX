
'''


@author: Dr. Leo
'''

from IPython.utils.traitlets import Unicode
from IPython.config.configurable import LoggingConfigurable


class Reader(LoggingConfigurable):
    
    def __init__(self, agency_id, client, **kwargs):
        super(Reader, self).__init__(**kwargs)
        self.client = client
        self.agency_id = agency_id
        
    
    def parse(self, source): raise NotImplemented
    
