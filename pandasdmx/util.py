from collections import OrderedDict

from traitlets import Dict, Undefined, SequenceTypes, is_trait, warn, repr_type


class DictLike(OrderedDict):
    """Container with features of a dict & list, plus attribute access."""
    def __getitem__(self, name):
        if isinstance(name, int):
            return list(self.values())[name]
        else:
            return super(OrderedDict, self).__getitem__(name)

    __getattr__ = OrderedDict.__getitem__
    __setattr__ = OrderedDict.__setitem__


class DictLikeTrait(Dict):
    """Container trait type using DictLike.

    __init__() is identical to traitlets.Dict.__init__() except for the very
    last line.
    """
    _trait = None

    def __init__(self, trait=None, traits=None, default_value=Undefined,
                 **kwargs):  # pragma: no cover
        # Handling positional arguments
        if default_value is Undefined and trait is not None:
            if not is_trait(trait):
                default_value = trait
                trait = None

        # Handling default value
        if default_value is Undefined:
            default_value = {}
        if default_value is None:
            args = None
        elif isinstance(default_value, dict):
            args = (default_value,)
        elif isinstance(default_value, SequenceTypes):
            args = (default_value,)
        else:
            raise TypeError('default value of Dict was %s' % default_value)

        # Case where a type of TraitType is provided rather than an instance
        if is_trait(trait):
            if isinstance(trait, type):
                warn("Traits should be given as instances, not types (for "
                     "example, `Int()`, not `Int`) Passing types is deprecated"
                     " in traitlets 4.1.",
                     DeprecationWarning, stacklevel=2)
            self._trait = trait() if isinstance(trait, type) else trait
        elif trait is not None:
            raise TypeError("`trait` must be a Trait or None, got %s" %
                            repr_type(trait))

        self._traits = traits

        super(Dict, self).__init__(klass=DictLike, args=args, **kwargs)

    def validate(self, obj, value):
        # Cast a dict to DictLike
        if isinstance(value, dict):
            new_val = DictLike()
            new_val.update(value)
            value = new_val
        return super(Dict, self).validate(obj, value)
