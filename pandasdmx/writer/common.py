
'''


@author: Dr. Leo
'''


from IPython.config.configurable import LoggingConfigurable


class BaseWriter(LoggingConfigurable):
    _input_types = []
    
    def __init__(self, **kwargs):
        super(BaseWriter, self).__init__(**kwargs)
        
    
    def initialize(self, source): raise NotImplemented
    
