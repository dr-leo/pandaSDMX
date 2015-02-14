
'''


@author: Dr. Leo
'''


from IPython.config.configurable import LoggingConfigurable


class BaseWriter(LoggingConfigurable):
    
    def __init__(self, msg, **kwargs):
        super(BaseWriter, self).__init__(**kwargs)
        self.msg = msg
        
    
    def initialize(self, source): raise NotImplemented
    
