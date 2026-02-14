import logging
import typing
from collections.abc import Iterator
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Mapping, Tuple, TypeVar, Union

import requests
try:
    import pydantic.v1 as pydantic
    from pydantic.v1 import Field, ValidationError, validator
    from pydantic.v1.class_validators import make_generic_validator
    from pydantic.v1.typing import get_origin
except Exception:
    import pydantic
    from pydantic import Field, ValidationError, validator
    from pydantic.class_validators import make_generic_validator
    try:
        from pydantic.typing import get_origin  # type: ignore [attr-defined]
    except Exception:  # pragma: no cover
        from typing import get_origin

try:
    import requests_cache
except ImportError:  # pragma: no cover
    HAS_REQUESTS_CACHE = False
else:
    HAS_REQUESTS_CACHE = True


KT = TypeVar("KT")
VT = TypeVar("VT")

log = logging.getLogger(__name__)

__all__ = [
    "BaseModel",
    "DictLike",
    "compare",
    "dictlike_field",
    "only",
    "summarize_dictlike",
    "validate_dictlike",
    "validator",
]


# Mapping from Resource value to class name.
CLASS_NAME = {
    "dataflow": "DataflowDefinition",
    "datastructure": "DataStructureDefinition",
}

# Inverse of :data:`CLASS_NAME`.
VALUE = {v: k for k, v in CLASS_NAME.items()}


class Resource(str, Enum):
    """Enumeration of SDMX-REST API resources.

    ============================= ======================================================
    :class:`Enum` member          :mod:`pandasdmx.model` class
    ============================= ======================================================
    ``actualconstraint``          :class:`.ContentConstraint`
    ``agencyscheme``              :class:`.AgencyScheme`
    ``allowedconstraint``         :class:`.ContentConstraint`
    ``attachementconstraint``     :class:`.AttachmentConstraint`
    ``categorisation``            :class:`.Categorisation`
    ``categoryscheme``            :class:`.CategoryScheme`
    ``codelist``                  :class:`.Codelist`
    ``conceptscheme``             :class:`.ConceptScheme`
    ``contentconstraint``         :class:`.ContentConstraint`
    ``data``                      :class:`.DataSet`
    ``dataflow``                  :class:`.DataflowDefinition`
    ``dataconsumerscheme``        :class:`.DataConsumerScheme`
    ``dataproviderscheme``        :class:`.DataProviderScheme`
    ``datastructure``             :class:`.DataStructureDefinition`
    ``organisationscheme``        :class:`.OrganisationScheme`
    ``provisionagreement``        :class:`.ProvisionAgreement`
    ``structure``                 Mixed.
    ----------------------------- ------------------------------------------------------
    ``customtypescheme``          Not implemented.
    ``hierarchicalcodelist``      Not implemented.
    ``metadata``                  Not implemented.
    ``metadataflow``              Not implemented.
    ``metadatastructure``         Not implemented.
    ``namepersonalisationscheme`` Not implemented.
    ``organisationunitscheme``    Not implemented.
    ``process``                   Not implemented.
    ``reportingtaxonomy``         Not implemented.
    ``rulesetscheme``             Not implemented.
    ``schema``                    Not implemented.
    ``structureset``              Not implemented.
    ``transformationscheme``      Not implemented.
    ``userdefinedoperatorscheme`` Not implemented.
    ``vtlmappingscheme``          Not implemented.
    ============================= ======================================================

    """

    actualconstraint = "actualconstraint"
    agencyscheme = "agencyscheme"
    allowedconstraint = "allowedconstraint"
    attachementconstraint = "attachementconstraint"
    categorisation = "categorisation"
    categoryscheme = "categoryscheme"
    codelist = "codelist"
    conceptscheme = "conceptscheme"
    contentconstraint = "contentconstraint"
    customtypescheme = "customtypescheme"
    data = "data"
    dataconsumerscheme = "dataconsumerscheme"
    dataflow = "dataflow"
    dataproviderscheme = "dataproviderscheme"
    datastructure = "datastructure"
    hierarchicalcodelist = "hierarchicalcodelist"
    metadata = "metadata"
    metadataflow = "metadataflow"
    metadatastructure = "metadatastructure"
    namepersonalisationscheme = "namepersonalisationscheme"
    organisationscheme = "organisationscheme"
    organisationunitscheme = "organisationunitscheme"
    process = "process"
    provisionagreement = "provisionagreement"
    reportingtaxonomy = "reportingtaxonomy"
    rulesetscheme = "rulesetscheme"
    schema = "schema"
    structure = "structure"
    structureset = "structureset"
    transformationscheme = "transformationscheme"
    userdefinedoperatorscheme = "userdefinedoperatorscheme"
    vtlmappingscheme = "vtlmappingscheme"

    @classmethod
    def from_obj(cls, obj):
        """Return an enumeration value based on the class of `obj`."""
        value = obj.__class__.__name__
        return cls[VALUE.get(value, value)]

    @classmethod
    def class_name(cls, value: "Resource", default=None) -> str:
        """Return the name of a :mod:`pandasdmx.model` class from an enum value.

        Values are returned in lower case.
        """
        return CLASS_NAME.get(value.value, value.value)

    @classmethod
    def describe(cls):
        return "{" + " ".join(v.name for v in cls._member_map_.values()) + "}"


#: Response codes defined by the SDMX-REST standard.
RESPONSE_CODE = {
    200: "OK",
    304: "No changes",
    400: "Bad syntax",
    401: "Unauthorized",
    403: "Semantic error",  # or "Forbidden"
    404: "Not found",
    406: "Not acceptable",
    413: "Request entity too large",
    414: "URI too long",
    500: "Internal server error",
    501: "Not implemented",
    503: "Unavailable",
}


class BaseModel(pydantic.BaseModel):
    """Common settings for :class:`pydantic.BaseModel` in :mod:`pandasdmx`."""

    class Config:
        copy_on_model_validation = 'none'
        validate_assignment = True


class MaybeCachedSession(type):
    """Metaclass to inherit from :class:`requests_cache.CachedSession`, if available.

    If :mod:`requests_cache` is not installed, returns :class:`requests.Session` as a
    base class.
    """

    def __new__(cls, name, bases, dct):
        base = (
            requests.Session if not HAS_REQUESTS_CACHE else requests_cache.CachedSession
        )
        return super().__new__(cls, name, (base,), dct)


KT = TypeVar("KT")
VT = TypeVar("VT")

log = logging.getLogger(__name__)

__all__ = [
    "BaseModel",
    "DictLike",
    "compare",
    "dictlike_field",
    "only",
    "summarize_dictlike",
    "validate_dictlike",
    "validator",
]


class DictLike(dict, typing.MutableMapping[KT, VT]):
    """Container with features of a dict & list, plus attribute access."""

    __slots__ = ("__dict__", "__field")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensures attribute access to dict items
        self.__dict__ = self

        # Reference to the pydantic.field.ModelField for the entries
        self.__field = None

    def __getitem__(self, key: Union[KT, int]) -> VT:
        """:meth:`dict.__getitem__` with integer access."""
        try:
            return super().__getitem__(key)
        except KeyError:
            if isinstance(key, int):
                # int() index access
                return list(self.values())[key]
            else:
                raise

    def __getstate__(self):
        """Exclude ``__field`` from items to be pickled."""
        return {"__dict__": self.__dict__}

    def __setitem__(self, key: KT, value: VT) -> None:
        """:meth:`dict.__setitem` with validation."""
        super().__setitem__(*self._validate_entry(key, value))

    def __copy__(self):
        # Construct explicitly to avoid returning the parent class, dict()
        return DictLike(**self)

    def copy(self):
        """Return a copy of the DictLike."""
        return self.__copy__()

    # pydantic compat

    @classmethod
    def __get_validators__(cls):
        yield cls._validate_whole

    @classmethod
    def _validate_whole(cls, v, field: pydantic.fields.ModelField):
        """Validate `v` as an entire DictLike object."""
        # Convert anything that can be converted to a dict(). pydantic internals catch
        # most other invalid types, e.g. set(); no need to handle them here.
        result = cls(v)

        # Reference to the pydantic.field.ModelField for the entries
        result.__field = field

        return result

    def _validate_entry(self, key, value):
        """Validate one `key`/`value` pair."""
        try:
            # Use pydantic's validation machinery
            v, error = self.__field._validate_mapping_like(
                ((key, value),), values={}, loc=(), cls=None
            )
        except AttributeError:
            # .__field is not populated
            return key, value
        else:
            if error:
                raise ValidationError([error], self.__class__)
            else:
                return (key, value)

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


# Utility methods for DictLike
#
# These are defined in separate functions to avoid collisions with keys and the
# attribute access namespace, e.g. if the DictLike contains keys "summarize" or
# "validate".


def dictlike_field():
    """Shorthand for :class:`pydantic.Field` with :class:`.DictLike` default factory."""
    return Field(default_factory=DictLike)


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


def validate_dictlike(cls):
    """Adjust `cls` so that its DictLike members are validated.

    This is necessary because DictLike is a subclass of :class:`dict`, and so
    :mod:`pydantic` fails to call :meth:`~DictLike.__get_validators__` and register
    those on BaseModels which include DictLike members.
    """
    # Iterate over annotated members of `cls`; only those which are DictLike
    for name, anno in filter(
        lambda item: get_origin(item[1]) is DictLike, cls.__annotations__.items()
    ):
        # Add the validator(s)
        field = cls.__fields__[name]
        field.post_validators = field.post_validators or []
        field.post_validators.extend(
            make_generic_validator(v) for v in DictLike.__get_validators__()
        )

    return cls


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


def only(iterator: Iterator) -> Any:
    """Return the only element of `iterator`, or :obj:`None`."""
    try:
        result = next(iterator)
        flag = object()
        assert flag is next(iterator, flag)
    except (StopIteration, AssertionError):
        return None  # 0 or ≥2 matches
    else:
        return result


def parse_content_type(value: str) -> Tuple[str, Dict[str, Any]]:
    """Return content type and parameters from `value`.

    Modified from :mod:`requests.util`.
    """
    tokens = value.split(";")
    content_type, params_raw = tokens[0].strip(), tokens[1:]
    params = {}
    to_strip = "\"' "

    for param in params_raw:
        k, *v = param.strip().split("=")

        if not k and not v:
            continue

        params[k.strip(to_strip).lower()] = v[0].strip(to_strip) if len(v) else True

    return content_type, params


@lru_cache()
def direct_fields(cls) -> Mapping[str, pydantic.fields.ModelField]:
    """Return the :mod:`pydantic` fields defined on `obj` or its class.

    This is like the ``__fields__`` attribute, but excludes the fields defined on any
    parent class(es).
    """
    return {
        name: info
        for name, info in cls.__fields__.items()
        if name not in set(cls.mro()[1].__fields__.keys())
    }


try:
    from typing import get_args  # type: ignore [attr-defined]
except ImportError:  # pragma: no cover
    # For Python <3.8
    def get_args(tp) -> Tuple[Any, ...]:
        return tp.__args__
