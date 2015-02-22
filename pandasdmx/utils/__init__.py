'''
module pandasdmx.utils - helper classes and functions

'''


from .aadict import aadict 
from collections import namedtuple
from itertools import chain
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
        
def chain_namedtuples(*nt):
    if len(nt) == 0:
        raise TypeError('Expected at least 1 argument, 0 given.')
    if len(nt) == 1: return nt
    fields = tuple(chain(*(i._fields for i in nt)))
    new_type = namedtuple_factory('Chained', fields)
    values = chain(*nt)
    return new_type._make(values)
       
            
# 2to3 compatibility
if sys.version[0] == '3': str_type = str
else: str_type = unicode 