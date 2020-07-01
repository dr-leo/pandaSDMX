import collections
import logging
import typing
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Type, TypeVar, Union, no_type_check

import pydantic
from pydantic import DictError, Extra, ValidationError, validator  # noqa: F401
from pydantic.class_validators import make_generic_validator

KT = TypeVar("KT")
VT = TypeVar("VT")

try:
    from typing import OrderedDict
except ImportError:
    # Python < 3.7.2 compatibility; see
    # https://github.com/python/cpython/commit/68b56d0
    from typing import _alias  # type: ignore

    OrderedDict = _alias(collections.OrderedDict, (KT, VT))


log = logging.getLogger(__name__)


class Resource(str, Enum):
    """Enumeration of SDMX REST API endpoints.

    ====================== ================================================
    :class:`Enum` member   :mod:`sdmx.model` class
    ====================== ================================================
    ``categoryscheme``     :class:`.CategoryScheme`
    ``codelist``           :class:`.Codelist`
    ``conceptscheme``      :class:`.ConceptScheme`
    ``data``               :class:`.DataSet`
    ``dataflow``           :class:`.DataflowDefinition`
    ``datastructure``      :class:`.DataStructureDefinition`
    ``provisionagreement`` :class:`.ProvisionAgreement`
    ====================== ================================================
    """

    # agencyscheme = 'agencyscheme'
    # attachementconstraint = 'attachementconstraint'
    # categorisation = 'categorisation'
    categoryscheme = "categoryscheme"
    codelist = "codelist"
    conceptscheme = "conceptscheme"
    # contentconstraint = 'contentconstraint'
    data = "data"
    # dataconsumerscheme = 'dataconsumerscheme'
    dataflow = "dataflow"
    # dataproviderscheme = 'dataproviderscheme'
    datastructure = "datastructure"
    # hierarchicalcodelist = 'hierarchicalcodelist'
    # metadata = 'metadata'
    # metadataflow = 'metadataflow'
    # metadatastructure = 'metadatastructure'
    # organisationscheme = 'organisationscheme'
    # organisationunitscheme = 'organisationunitscheme'
    # process = 'process'
    provisionagreement = "provisionagreement"
    # reportingtaxonomy = 'reportingtaxonomy'
    # schema = 'schema'
    # structure = 'structure'
    # structureset = 'structureset'

    @classmethod
    def from_obj(cls, obj):
        """Return an enumeration value based on the class of *obj*."""
        clsname = {"DataStructureDefinition": "datastructure"}.get(
            obj.__class__.__name__, obj.__class__.__name__
        )
        return cls[clsname.lower()]

    @classmethod
    def describe(cls):
        return "{" + " ".join(v.name for v in cls._member_map_.values()) + "}"


if TYPE_CHECKING:
    Model = TypeVar("Model", bound="BaseModel")


class BaseModel(pydantic.BaseModel):
    """Shim for pydantic.BaseModel.

    This class changes two behaviours in pydantic. The methods are direct
    copies from pydantic's code, with marked changes.

    1. https://github.com/samuelcolvin/pydantic/issues/524

       - "Multiple RecursionErrors with self-referencing models"
       - In e.g. :class:`.Item`, having both .parent and .child references
         leads to infinite recursion during validation.
       - Fix: override BaseModel.__setattr__.
       - New value 'limited' for Config.validate_assignment: no sibling
         field values are passed to Field.validate().
       - New key Config.validate_assignment_exclude: list of field names that
         are not validated per se *and* not passed to Field.validate() when
         validating a sibling field.
    2. https://github.com/samuelcolvin/pydantic/issues/521

       - "Assignment to attribute changes id() but not referenced object,"
         marked as wontfix by pydantic maintainer.
       - When cls.attr is typed as BaseModel (or a subclass), then
         a.attr is b.attr is always False, even when set to the same reference.
       - Fix: override BaseModel.validate() without copy().
    """

    class Config:
        validate_assignment = "limited"
        validate_assignment_exclude: List[str] = []

    # Workaround for https://github.com/samuelcolvin/pydantic/issues/521
    @classmethod
    def validate(cls: Type["Model"], value: Any) -> "Model":
        if isinstance(value, dict):
            return cls(**value)
        elif isinstance(value, cls):
            return value  # ***
        elif cls.__config__.orm_mode:
            return cls.from_orm(value)
        else:
            try:
                value_as_dict = dict(value)
            except (TypeError, ValueError) as e:
                raise DictError() from e
            return cls(**value_as_dict)

    # Workaround for https://github.com/samuelcolvin/pydantic/issues/524
    @no_type_check
    def __setattr__(self, name, value):
        if self.__config__.extra is not Extra.allow and name not in self.__fields__:
            raise ValueError(
                f'"{self.__class__.__name__}" object has no field' f' "{name}"'
            )
        elif not self.__config__.allow_mutation:
            raise TypeError(
                f'"{self.__class__.__name__}" is immutable and '
                "does not support item assignment"
            )
        elif (
            self.__config__.validate_assignment
            and name not in self.__config__.validate_assignment_exclude
        ):
            if self.__config__.validate_assignment == "limited":
                kw = {"include": {}}
            else:
                kw = {"exclude": {name}}
            known_field = self.__fields__.get(name, None)
            if known_field:
                value, error_ = known_field.validate(value, self.dict(**kw), loc=name)
                if error_:
                    raise ValidationError([error_], type(self))
        self.__dict__[name] = value
        self.__fields_set__.add(name)


class DictLike(collections.OrderedDict, typing.MutableMapping[KT, VT]):
    """Container with features of a dict & list, plus attribute access."""

    def __getitem__(self, key: Union[KT, int]) -> VT:
        try:
            return super().__getitem__(key)
        except KeyError:
            if isinstance(key, int):
                return list(self.values())[key]
            elif isinstance(key, str) and key.startswith("__"):
                raise AttributeError
            else:
                raise

    def __setitem__(self, key: KT, value: VT) -> None:
        key = self._apply_validators("key", key)
        value = self._apply_validators("value", value)
        super().__setitem__(key, value)

    # Access items as attributes
    def __getattr__(self, name) -> VT:
        try:
            return self.__getitem__(name)
        except KeyError as e:
            raise AttributeError(*e.args) from None

    def validate(cls, value, field):
        if not isinstance(value, (dict, DictLike)):
            raise ValueError(value)

        result = DictLike()
        result.__fields = {"key": field.key_field, "value": field}
        result.update(value)
        return result

    def _apply_validators(self, which, value):
        try:
            field = self.__fields[which]
        except AttributeError:
            return value
        result, error = field._apply_validators(
            value, validators=field.validators, values={}, loc=(), cls=None
        )
        if error:
            raise ValidationError([error], self.__class__)
        else:
            return result

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two DictLike instances are identical if they contain the same set of keys, and
        corresponding values compare equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`compare` for the values.
        """
        if set(self.keys()) != set(other.keys()):
            log.info(f"Not identical: {sorted(self.keys())} / {sorted(other.keys())}")
            return False

        for key, value in self.items():
            if not value.compare(other[key], strict):
                return False

        return True


def summarize_dictlike(dl, maxwidth=72):
    """Return a string summary of the DictLike contents."""
    value_cls = dl[0].__class__.__name__
    count = len(dl)
    keys = " ".join(dl.keys())
    result = f"{value_cls} ({count}): {keys}"

    if len(result) > maxwidth:
        # Truncate the list of keys
        result = result[: maxwidth - 3] + "..."

    return result


def validate_dictlike(*fields):
    def decorator(cls):
        v = make_generic_validator(DictLike.validate)
        for field in fields:
            cls.__fields__[field].post_validators = [v]
        return cls

    return decorator


def compare(attr, a, b, strict: bool) -> bool:
    """Return :obj:`True` if ``a.attr`` == ``b.attr``.

    If strict is :obj:`False`, :obj:`None` is permissible as `a` or `b`; otherwise,
    """
    return getattr(a, attr) == getattr(b, attr) or (
        not strict and None in (getattr(a, attr), getattr(b, attr))
    )
    # if not result:
    #     log.info(f"Not identical: {attr}={getattr(a, attr)} / {getattr(b, attr)}")
    # return result
