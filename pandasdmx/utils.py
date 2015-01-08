'''
module pandasdmx.utils - helper classes and functions

'''


from IPython.utils.traitlets import HasTraits, Any
from IPython.config.loader import Config 
from collections import namedtuple
import sys

class DictLike(Config): pass

class NamedTupleFactory:
    """
Wrap namedtuple function from the collections stdlib module
to return a singleton if a nametuple with the same field names
has already been created. 
    """
    
    cache = {}
        
    def get(self, fields):
        """
        return a subclass of tuple instance as does namedtuple
        """

        fields = tuple(fields)
        if not fields in self.cache: 
            self.cache[fields] = namedtuple(
                'SDMXMetadata', fields)
        return self.cache[fields]
    


class HasItems:
    _items = None
     
    
    def __init__(self, *args, items = [], **kwargs):
        super(HasItems, self).__init__(*args, **kwargs)
        self._items = items
    
    def append(self, item):        return self._items.append(item) 
            
    def remove(self, item):
        return self._items.remove(item) 
                
    def __iter__(self):
        return self[:]
        
    def __setitem__(self, item, value):
        return self._items.__setitem__(item, value)
    
    def __getitem__(self, item):
        if isinstance(item, str_type):
            return self._item_by_id(item)
        elif isinstance(item, int):
            return self._item_by_index(item)
        elif isinstance(item, slice):
            return self._items_by_slice(item) 
        

    def __len__(self):
        return len(list(self))
        
# 2to3 compatibility
if sys.version[0] == '3': str_type = str
else: str_type = unicode 