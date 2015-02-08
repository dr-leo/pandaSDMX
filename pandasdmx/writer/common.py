
'''


@author: Dr. Leo
'''


from IPython.config.configurable import LoggingConfigurable


class Writer(LoggingConfigurable):
    _input_types = []
    
    def __init__(self, request, **kwargs):
        super(Writer, self).__init__(**kwargs)
        self.request = request
        
    
    def initialize(self, source): raise NotImplemented
    
