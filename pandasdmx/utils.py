'''
module pandasdmx.utils - helper classes and functions

'''


from aadict import aadict 
from collections import namedtuple
import sys

class DictLike(aadict):
    
    def findname(self, search_str, language = 'en'):
        '''
        return new DictLike of items where 'search_str' is a substring of 'name'
        in the specified language (defaults to 'en'). self.values() should therefore contain model.NameableArtefact subclass instances.
        Any capitalization is disregarded. Hence 'a' == 'A'.
        '''
        s = search_str.lower()
        return DictLike(result for result in self.items() 
                        if s in result[1].name[language].lower())
        
        

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
    
        
# 2to3 compatibility
if sys.version[0] == '3': str_type = str
else: str_type = unicode 