# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
    This module contains the base class for readers.

'''

from pandasdmx.utils import DictLike


class BaseReader:

    def __init__(self, request, **kwargs):
        self.request = request
        # subclasses must declare '_compiled' flag and '_paths' dict
        # and '_compile_paths' function
        # Check if we need to compile path expressions
        if not self._compiled:
            self._compile_paths()
            self.__class__._compiled = True

    def initialize(self, source):
        raise NotImplemented

    def read_identifiables(self, cls,  sdmxobj, offset=None):
        '''
        If sdmxobj inherits from dict: update it  with modelized elements.
        These must be instances of model.IdentifiableArtefact,
        i.e. have an 'id' attribute. This will be used as dict keys.
        If sdmxobj does not inherit from dict: return a new DictLike.
        '''
        path = self._paths[cls]
        if offset:
            try:
                base = self._paths[offset](sdmxobj._elem)[0]
            except IndexError:
                return None
        else:
            base = sdmxobj._elem
        result = {e.get('id'): cls(self, e) for e in path(base)}
        if isinstance(sdmxobj, dict):
            sdmxobj.update(result)
        else:
            return DictLike(result)

    def read_instance(self, cls, sdmxobj, offset=None, first_only=True):
        '''
        If cls in _paths and matches,
        return an instance of cls with the first XML element,
        or, if first_only is False, a list of cls instances 
        for all elements found,
        If no matches were found, return None.  
        '''
        if offset:
            try:
                base = self._paths[offset](sdmxobj._elem)[0]
            except IndexError:
                return None
        else:
            base = sdmxobj._elem
        result = self._paths[cls](base)
        if result:
            if first_only:
                return cls(self, result[0])
            else:
                return [cls(self, i) for i in result]

    def read_as_str(self, name, sdmxobj, first_only=True):
        result = self._paths[name](sdmxobj._elem)
        if result:
            if first_only:
                return result[0]
            else:
                return result
