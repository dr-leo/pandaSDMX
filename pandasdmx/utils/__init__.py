'''
module pandasdmx.utils - helper classes and functions

'''


from .aadict import aadict 
from collections import namedtuple
import sys

class DictLike(aadict):
    
     
    @property
    def aslist(self):
        return list(self.values()) 
        

        

class NamedTupleFactory:
    """
Wrap namedtuple function from the collections stdlib module
to return a singleton if a nametuple with the same field names
has already been created. 
    """
    
    cache = {}
        
    def __call__(self, name, fields):
        """
        return a subclass of tuple instance as does namedtuple
        """

        fields = tuple(fields)
        if not fields in self.cache: 
            self.cache[fields] = namedtuple(
                name, fields)
        return self.cache[fields]
    
namedtuple_factory = NamedTupleFactory()    
        
        
# 2to3 compatibility
if sys.version[0] == '3': str_type = str
else: str_type = unicode 