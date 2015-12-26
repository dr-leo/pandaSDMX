# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
module pandasdmx.utils - helper classes and functions

'''


from .aadict import aadict
from pandasdmx.utils.anynamedtuple import namedtuple
from itertools import chain
import sys


class DictLike(aadict):

    '''Thin wrapper around dict type

    It allows attribute-like item access, has a :meth:`find` method and inherits other
    useful features from aadict.
    '''

    def aslist(self):
        '''
        return values() as unordered list
        '''
        return list(self.values())

    def any(self):
        '''
        return an arbitrary or the only value. If dict is empty,
        raise KeyError.
        '''
        try:
            return next(iter(self.values()))
        except StopIteration:
            raise KeyError('DictLike is empty.')

    def find(self, search_str, by='name', language='en'):
        '''Select values by attribute

        Args:

            searchstr(str): the string to search for
            by(str): the name of the attribute to search by, defaults to 'name'
                The specified attribute must be either a string
                or a dict mapping language codes to strings.
                Such attributes occur, e.g. in :class:`pandasdmx.model.NameableArtefact` which is
                a base class for :class:`pandasdmx.model.DataFlowDefinition` and many others.
            language(str): language code specifying the language of the text to be searched, defaults to 'en'

        Returns:
            DictLike: items where value.<by> contains the search_str. International strings
                stored as dict with language codes as keys are
                searched. Capitalization is ignored.

        '''

        s = search_str.lower()
        # We distinguish between international strings stored as dict such as
        # name.en, name.fr, and normal strings.
        if by in ['name', 'description']:
            get_field = lambda obj: getattr(obj, by)[language]
        else:  # normal string
            get_field = lambda obj: getattr(obj, by)
        return DictLike(result for result in self.items()
                        if s in get_field(result[1]).lower())


class NamedTupleFactory:

    """
Wrap namedtuple function from the collections stdlib module
to return a singleton if a nametuple with the same field names
has already been created.
    """

    cache = {}

    def __call__(self, name, fields):
        """
        return namedtuple class as singleton 
        """

        fields = tuple(fields)
        if not fields in self.cache:
            self.cache[fields] = namedtuple(
                name, fields)
        return self.cache[fields]

namedtuple_factory = NamedTupleFactory()


def concat_namedtuples(*tup, **kwargs):
    '''
    Concatenate 2 or more namedtuples. The new namedtuple type
    is provided by :class:`NamedTupleFactory`
    return new namedtuple instance
    '''
    name = kwargs['name'] if 'name' in kwargs else None

    # filter out empty elements
    filtered = [i for i in filter(None, tup)]
    if filtered:
        if len(filtered) == 1:
            return filtered[0]
        else:
            fields = chain(*(t._fields for t in filtered))
            values = chain(*(t for t in filtered))
            if not name:
                name = 'SDMXNamedTuple'
            ConcatType = namedtuple_factory(name, fields)
            return ConcatType(*values)
    else:
        return ()


# 2to3 compatibility
if sys.version[0] == '3':
    str_type = str
else:
    str_type = unicode
