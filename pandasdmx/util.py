from enum import Enum
from typing import (
    KT,
    VT,
    Union,
    get_type_hints,
    no_type_check,
    )
try:
    from typing import OrderedDict
except ImportError:
    # Python < 3.7.2 compatibility; see
    # https://github.com/python/cpython/commit/68b56d0
    import collections
    from typing import _alias
    OrderedDict = _alias(collections.OrderedDict, (KT, VT))


import pydantic
from pydantic import DictError, Extra, ValidationError
from pydantic.class_validators import make_generic_validator
from pydantic.utils import change_exception


class Resource(str, Enum):
    """Enumeration of SDMX REST API endpoints.

    ====================== ================================================
    :class:`Enum` member   :mod:`pandasdmx.model` class
    ====================== ================================================
    ``categoryscheme``     :class:`CategoryScheme \
                                   <pandasdmx.model.CategoryScheme>`
    ``codelist``           :class:`Codelist \
                                   <pandasdmx.model.Codelist>`
    ``conceptscheme``      :class:`ConceptScheme \
                                   <pandasdmx.model.ConceptScheme>`
    ``data``               :class:`DataSet \
                                   <pandasdmx.model.DataSet>`
    ``dataflow``           :class:`DataflowDefinition \
                                   <pandasdmx.model.DataflowDefinition>`
    ``datastructure``      :class:`DataStructureDefinition \
                                   <pandasdmx.model.DataStructureDefinition>`
    ``provisionagreement`` :class:`ProvisionAgreement \
                                   <pandasdmx.model.ProvisionAgreement>`
    ====================== ================================================
    """

    # agencyscheme = 'agencyscheme'
    # attachementconstraint = 'attachementconstraint'
    # categorisation = 'categorisation'
    categoryscheme = 'categoryscheme'
    codelist = 'codelist'
    conceptscheme = 'conceptscheme'
    # contentconstraint = 'contentconstraint'
    data = 'data'
    # dataconsumerscheme = 'dataconsumerscheme'
    dataflow = 'dataflow'
    # dataproviderscheme = 'dataproviderscheme'
    datastructure = 'datastructure'
    # hierarchicalcodelist = 'hierarchicalcodelist'
    # metadata = 'metadata'
    # metadataflow = 'metadataflow'
    # metadatastructure = 'metadatastructure'
    # organisationscheme = 'organisationscheme'
    # organisationunitscheme = 'organisationunitscheme'
    # process = 'process'
    provisionagreement = 'provisionagreement'
    # reportingtaxonomy = 'reportingtaxonomy'
    # schema = 'schema'
    # structure = 'structure'
    # structureset = 'structureset'

    @classmethod
    def from_obj(cls, obj):
        """Return an enumeration value based on the class of *obj*."""
        clsname = {
            'DataStructureDefinition': 'datastructure',
            }.get(obj.__class__.__name__, obj.__class__.__name__)
        return cls[clsname.lower()]

    @classmethod
    def describe(cls):
        return '{' + ' '.join(v.name for v in cls._member_map_.values()) + '}'


class BaseModel(pydantic.BaseModel):
    class Config:
        validate_assignment = 'limited'
        validate_assignment_exclude = []

    # Workaround for https://github.com/samuelcolvin/pydantic/issues/521:
    # - When cls.attr is typed as BaseModel (or a subclass), then
    #   a.attr is b.attr is always False, even when set to the same reference
    # - Same as pydantic.BaseModel.validate, but without copy().
    # - Issue marked as wontfix by pydantic maintainer.
    @classmethod
    def validate(cls, value):
        """Same as pydantic.BaseModel, but without copy()."""
        if isinstance(value, dict):
            return cls(**value)
        elif isinstance(value, cls):
            return value
        else:
            with change_exception(DictError, TypeError, ValueError):
                return cls(**dict(value))  # type: ignore

    # Workaround for https://github.com/samuelcolvin/pydantic/issues/524:
    @no_type_check
    def __setattr__(self, name, value):
        if (self.__config__.extra is not Extra.allow and name not in
                self.__fields__):
            raise ValueError(f'"{self.__class__.__name__}" object has no '
                             f'field "{name}"')
        elif not self.__config__.allow_mutation:
            raise TypeError(f'"{self.__class__.__name__}" is immutable and '
                            f'does not support item assignment')
        elif (self.__config__.validate_assignment and name not in
              self.__config__.validate_assignment_exclude):
            if self.__config__.validate_assignment == 'limited':
                kw = {'include': {}}
            else:
                kw = {'exclude': {name}}
            value_, error_ = self.fields[name].validate(value, self.dict(**kw),
                                                        loc=name)
            if error_:
                raise ValidationError([error_])
            else:
                self.__values__[name] = value_
                self.__fields_set__.add(name)
        else:
            self.__values__[name] = value
            self.__fields_set__.add(name)


def get_class_hint(obj, attr):
    klass = get_type_hints(obj.__class__)[attr].__args__[0]
    if getattr(klass, '__origin__', None) is Union:
        klass = klass.__args__[0]
    return klass


class DictLike(OrderedDict[KT, VT]):
    """Container with features of a dict & list, plus attribute access."""
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            if isinstance(key, int):
                return list(self.values())[key]
            elif isinstance(key, str) and key.startswith('__'):
                raise AttributeError
            else:
                raise

    def __setitem__(self, key, value):
        key = self._apply_validators('key', key)
        value = self._apply_validators('value', value)
        super().__setitem__(key, value)

    # Access items as attributes
    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError as e:
            raise AttributeError(*e.args) from None

    def validate(cls, value, field):
        if not isinstance(value, (dict, DictLike)):
            raise ValueError(value)

        result = DictLike()
        result.__fields = {'key': field.key_field, 'value': field}
        result.update(value)
        return result

    def _apply_validators(self, which, value):
        try:
            field = self.__fields[which]
        except AttributeError:
            return value
        result, error = field._apply_validators(
            value, validators=field.validators, values={}, loc=(), cls=None)
        if error:
            raise ValidationError([error])
        else:
            return result


def summarize_dictlike(dl, maxwidth=72):
    """Return a string summary of the DictLike contents."""
    value_cls = dl[0].__class__.__name__
    count = len(dl)
    keys = ' '.join(dl.keys())
    result = f'{value_cls} ({count}): {keys}'

    if len(result) > maxwidth:
        # Truncate the list of keys
        result = result[:maxwidth - 3] + '...'

    return result


def validate_dictlike(*fields):
    def decorator(cls):
        v = make_generic_validator(DictLike.validate)
        for field in fields:
            cls.__fields__[field].whole_post_validators = [v]
        return cls

    return decorator
