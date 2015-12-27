import sys as _sys
from operator import itemgetter as _itemgetter, eq as _eq
from keyword import iskeyword as _iskeyword

# 2to3 helpers


def _isidentifier3(name):
    return name.isidentifier()


def _isidentifier2(name):
    if (name[0].isdigit()
            or [c for c in name if not (c.isalnum() or c == '_')]):
        return False
    else:
        return True

if _sys.version.startswith('3'):
    _isidentifier = _isidentifier3
else:
    _isidentifier = _isidentifier2


##########################################################################
# namedtuple
##########################################################################

_class_template = """\
from pandasdmx.utils import str_type
from operator import itemgetter as _itemgetter
from collections import OrderedDict

class {typename}(tuple):
    '{typename}({arg_list})'

    __slots__ = ()

    _fields = {field_names!r}

    def __new__(_cls, {arg_list}):
        'Create new instance of {typename}({arg_list})'
        return tuple.__new__(_cls, ({arg_list}))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new {typename} object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != {num_fields:d}:
            raise TypeError('Expected {num_fields:d} arguments, got %d' % len(result))
        return result

    def _replace(_self, **kwds):
        'Return a new {typename} object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, {field_names!r}, _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % list(kwds))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + '({repr_fmt})' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values.'
        return OrderedDict(zip(self._fields, self))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)

    def __getitem__(self, key):
        if isinstance(key, str_type):
            return super({typename}, self).__getitem__(self._fields.index(key))
        else:
            return super({typename}, self).__getitem__(key)
             
            
{field_defs}
"""

_repr_template = '{name}=%r'

_field_template = '''\
    {name} = property(_itemgetter({index:d}), doc='Alias for field number {index:d}')
'''


def namedtuple(typename, field_names, verbose=False, rename=False):
    """Returns a new subclass of tuple with named fields.
    This is a patched version of collections.namedtuple from the stdlib.
    Unlike the latter, it accepts non-identifier strings as field names.
    All values are accessible through dict syntax. Fields whose names are
    identifiers are also accessible via attribute syntax as in ordinary namedtuples, alongside traditional
    indexing. This feature is needed as SDMX allows field names
    to contain '-'. 

    >>> Point = namedtuple('Point', ['x', 'y'])
    >>> Point.__doc__                   # docstring for the new class
    'Point(x, y)'
    >>> p = Point(11, y=22)             # instantiate with positional args or keywords
    >>> p[0] + p[1]                     # indexable like a plain tuple
    33
    >>> x, y = p                        # unpack like a regular tuple
    >>> x, y
    (11, 22)
    >>> p.x + p.y                       # fields also accessable by name
    33
    >>> d = p._asdict()                 # convert to a dictionary
    >>> d['x']
    11
    >>> Point(**d)                      # convert from a dictionary
    Point(x=11, y=22)
    >>> p._replace(x=100)               # _replace() is like str.replace() but targets named fields
    Point(x=100, y=22)

    """

    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = str(typename)
    for name in [typename] + field_names:
        if type(name) != str:
            raise TypeError('Type names and field names must be strings')
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             'keyword: %r' % name)
    if not _isidentifier(typename):
        raise ValueError('Type names must be valid '
                         'identifiers: %r' % name)
    seen = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: '
                             '%r' % name)
        if name in seen:
            raise ValueError('Encountered duplicate field name: %r' % name)
        seen.add(name)
    arg_names = ['_' + str(i) for i in range(len(field_names))]
    # Fill-in the class template
    class_definition = _class_template.format(
        typename=typename,
        field_names=tuple(field_names),
        num_fields=len(field_names),
        arg_list=repr(tuple(arg_names)).replace("'", "")[1:-1],
        repr_fmt=', '.join(_repr_template.format(name=name)
                           for name in field_names),
        field_defs='\n'.join(_field_template.format(index=index, name=name)
                             for index, name in enumerate(field_names) if _isidentifier(name))
    )

    # Execute the template string in a temporary namespace and support
    # tracing utilities by setting a value for frame.f_globals['__name__']
    namespace = dict(__name__='namedtuple_%s' % typename)
    exec(class_definition, namespace)
    result = namespace[typename]
    result._source = class_definition
    if verbose:
        print(result._source)

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython).
    try:
        result.__module__ = _sys._getframe(
            1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return result
