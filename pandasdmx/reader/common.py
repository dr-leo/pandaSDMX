
'''


@author: Dr. Leo
'''


from IPython.config.configurable import LoggingConfigurable


class Reader(LoggingConfigurable):
    
    def __init__(self, request, **kwargs):
        super(Reader, self).__init__(**kwargs)
        self.request = request
        
    
    def initialize(self, source): raise NotImplemented
    
