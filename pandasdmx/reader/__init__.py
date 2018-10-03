# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
    This module contains the abstract base class for readers.

'''
from abc import ABC, abstractmethod

from pandasdmx.utils import DictLike


class BaseReader(ABC):

    def __init__(self, request, **kwargs):
        self.request = request
        self._compile_paths()

    @classmethod
    def _compile_paths(cls):
        """Compile path expressions.

        Subclasses MAY declare a _paths dict, in which case they MUST implement
        _compile_paths() that compiles these paths *only once*. To avoid
        repeated compilation, they can:
        - set and check an attribute like _compiled,
        - check the type of a value in _paths, or
        - anything else.
        """
        if hasattr(cls, '_paths'):
            raise NotImplemented

    @abstractmethod
    def initialize(self, source):
        """Initialize the reader.

        Must return an instance of model.Message or a subclass.
        """
        pass

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
