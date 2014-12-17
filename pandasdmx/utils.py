'''
module pandasdmx.utils - helper classes and functions




'''


from IPython.utils.traitlets import HasTraits 

class IsIterable(HasTraits):
    _items = Any 
    
    def __init__(self, *args, items = [], **kwargs):
        super(IsIterable, self).__init__(*args, **kwargs)
        self._items = items
    
    def append(self, item):
        return self._items.append(item) 
            
    def remove(self, item):
        return self._items.remove(item) 
                
    def __iter__(self):
        # handle iterables and generator functions
        try:
            return self._items.__iter__()
        except AttributeError:
            return self._items().__iter__()
        
    def __setitem__(self, item, value):
        return self._items.__setitem__(item, value)
        
    def __getitem__(self, item):
        return self._items.__getitem__(item)

    def __len__(self):
        return self._items.__len__()
        
