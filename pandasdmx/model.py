"""SDMX Information Model (SDMX-IM).

This module implements many of the classes described in the SDMX-IM specification
('spec'), which is available from:

- https://sdmx.org/?page_id=5008
- https://sdmx.org/wp-content/uploads/
    SDMX_2-1-1_SECTION_2_InformationModel_201108.pdf

Details of the implementation:

- Python typing and pydantic are used to enforce the types of attributes that reference
  instances of other classes.
- Some classes have convenience attributes not mentioned in the spec, to ease navigation
  between related objects. These are marked “:mod:`sdmx` extension not in the IM.”
- Class definitions are grouped by section of the spec, but these sections appear out
  of order so that dependent classes are defined first.

"""
# TODO for complete implementation of the IM, enforce TimeKeyValue (instead of KeyValue)
#      for {Generic,StructureSpecific} TimeSeriesDataSet.

import logging
from collections import ChainMap
from collections.abc import Collection
from collections.abc import Iterable as IterableABC
from copy import copy
from datetime import date, datetime, timedelta
from enum import Enum
from functools import lru_cache
from inspect import isclass
from itertools import product
from operator import attrgetter, itemgetter
from typing import (
    Any,
    Dict,
    Generator,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from warnings import warn

from pandasdmx.util import (
    BaseModel,
    DictLike,
    compare,
    dictlike_field,
    only,
    Resource,
    validate_dictlike,
    validator,
)

log = logging.getLogger(__name__)

# TODO read this from the environment, or use any value set in the SDMX-ML spec.
#      Currently set to 'en' because test_dsd.py expects it.
DEFAULT_LOCALE = "en"


# §3.2: Base structures


class InternationalString:
    """SDMX-IM InternationalString.

    SDMX-IM LocalisedString is not implemented. Instead, the 'localizations' is a
    mapping where:

     - keys correspond to the 'locale' property of LocalisedString.
     - values correspond to the 'label' property of LocalisedString.

    When used as a type hint with pydantic, InternationalString fields can be assigned
    to in one of four ways::

        class Foo(BaseModel):
             name: InternationalString = InternationalString()

        # Equivalent: no localizations
        f = Foo()
        f = Foo(name={})

        # Using an explicit locale
        f.name['en'] = "Foo's name in English"

        # Using a (locale, label) tuple
        f.name = ('fr', "Foo's name in French")

        # Using a dict
        f.name = {'en': "Replacement English name",
                  'fr': "Replacement French name"}

        # Using a bare string, implicitly for the DEFAULT_LOCALE
        f.name = "Name in DEFAULT_LOCALE language"

    Only the first method preserves existing localizations; the latter three replace
    them.

    """

    localizations: Dict[str, str] = {}

    def __init__(self, value=None, **kwargs):
        super().__init__()

        # Handle initial values according to type
        if isinstance(value, str):
            # Bare string
            value = {DEFAULT_LOCALE: value}
        elif (
            isinstance(value, Collection)
            and len(value) == 2
            and isinstance(value[0], str)
        ):
            # 2-tuple of str is (locale, label)
            value = {value[0]: value[1]}
        elif isinstance(value, dict):
            # dict; use directly
            pass
        elif isinstance(value, IterableABC):
            # Iterable of 2-tuples
            value = {locale: label for (locale, label) in value}
        elif value is None:
            # Keyword arguments → dict, possibly empty
            value = dict(kwargs)
        else:
            raise ValueError(value, kwargs)

        self.localizations = value

    # Convenience access
    def __getitem__(self, locale):
        return self.localizations[locale]

    def __setitem__(self, locale, label):
        self.localizations[locale] = label

    # Duplicate of __getitem__, to pass existing tests in test_dsd.py
    def __getattr__(self, name):
        try:
            return self.__dict__["localizations"][name]
        except KeyError:
            raise AttributeError(name) from None

    def __add__(self, other):
        result = copy(self)
        result.localizations.update(other.localizations)
        return result

    def localized_default(self, locale=None):
        """Return the string in *locale* if not  empty, or else the first defined."""
        if locale and (locale in self.localizations) and self.localizations[locale]:  
            return self.localizations[locale]
        if len(self.localizations):
            # No label in the default locale; use the first stored non-empty str value
            return next(filter(None, self.localizations.values()))
        else:
            return ""

    def __str__(self):
        return self.localized_default(DEFAULT_LOCALE)

    def __repr__(self):
        return "\n".join(
            ["{}: {}".format(*kv) for kv in sorted(self.localizations.items())]
        )

    def __eq__(self, other):
        try:
            return self.localizations == other.localizations
        except AttributeError:
            return NotImplemented

    @classmethod
    def __get_validators__(cls):
        yield cls.__validate

    @classmethod
    def __validate(cls, value, values, config, field):
        # Any value that the constructor can handle can be assigned
        if not isinstance(value, InternationalString):
            value = InternationalString(value)

        try:
            # Update existing value
            existing = values[field.name]
            existing.localizations.update(value.localizations)
            return existing
        except KeyError:
            # No existing value/None; return the assigned value
            return value


class Annotation(BaseModel):
    #: Can be used to disambiguate multiple annotations for one AnnotableArtefact.
    id: Optional[str] = None
    #: Title, used to identify an annotation.
    title: Optional[str] = None
    #: Specifies how the annotation is processed.
    type: Optional[str] = None
    #: A link to external descriptive text.
    url: Optional[str] = None

    #: Content of the annotation.
    text: InternationalString = InternationalString()


class AnnotableArtefact(BaseModel):
    #: :class:`Annotations <.Annotation>` of the object.
    #:
    #: :mod:`pandaSDMX` implementation: The IM does not specify the name of this
    #: feature.
    annotations: List[Annotation] = []

    def get_annotation(self, **attrib):
        """Return a :class:`Annotation` with given `attrib`, e.g. 'id'.

        If more than one `attrib` is given, all must match a particular annotation.

        Raises
        ------
        KeyError
            If there is no matching annotation.
        """
        for anno in self.annotations:
            if all(getattr(anno, key, None) == value for key, value in attrib.items()):
                return anno

        raise KeyError(attrib)

    def pop_annotation(self, **attrib):
        """Remove and return a :class:`Annotation` with given `attrib`, e.g. 'id'.

        If more than one `attrib` is given, all must match a particular annotation.

        Raises
        ------
        KeyError
            If there is no matching annotation.
        """
        for i, anno in enumerate(self.annotations):
            if all(getattr(anno, key, None) == value for key, value in attrib.items()):
                return self.annotations.pop(i)

        raise KeyError(attrib)


class _MissingID(str):
    def __str__(self):
        return "(missing id)"

    def __eq__(self, other):
        return isinstance(other, self.__class__)


MissingID = _MissingID()


class IdentifiableArtefact(AnnotableArtefact):
    #: Unique identifier of the object.
    id: str = MissingID
    #: Universal resource identifier that may or may not be resolvable.
    uri: Optional[str] = None
    #: Universal resource name. For use in SDMX registries; all registered
    #: objects have a URN.
    urn: Optional[str] = None

    urn_group: Dict = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.urn:
            import pandasdmx.urn

            self.urn_group = pandasdmx.urn.match(self.urn)

        try:
            if self.id not in (self.urn_group["item_id"] or self.urn_group["id"]):
                raise ValueError(f"ID {self.id} does not match URN {self.urn}")
        except KeyError:
            pass

    def __eq__(self, other):
        """Equality comparison.

        IdentifiableArtefacts can be compared to other instances. For convenience, a
        string containing the object's ID is also equal to the object.
        """
        if isinstance(other, self.__class__):
            return self.id == other.id
        elif isinstance(other, str):
            return self.id == other

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two IdentifiableArtefacts are the same if they have the same :attr:`id`,
        :attr:`uri`, and :attr:`urn`.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return (
            compare("id", self, other, strict)
            and compare("uri", self, other, strict)
            and compare("urn", self, other, strict)
        )

    def __hash__(self):
        return id(self) if self.id == MissingID else hash(self.id)

    def __lt__(self, other):
        return (
            self.id < other.id if isinstance(other, self.__class__) else NotImplemented
        )

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class NameableArtefact(IdentifiableArtefact):
    #: Multi-lingual name of the object.
    name: InternationalString = InternationalString()
    #: Multi-lingual description of the object.
    description: InternationalString = InternationalString()

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two NameableArtefacts are the same if:

        - :meth:`.IdentifiableArtefact.compare` is :obj:`True`, and
        - they have the same :attr:`name` and :attr:`description`.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare` and :meth:`.IdentifiableArtefact.compare`.
        """
        if not super().compare(other, strict):
            pass
        elif self.name != other.name:
            log.debug(
                f"Not identical: name <{repr(self.name)}> != <{repr(other.name)}>"
            )
        elif self.description != other.description:
            log.debug(
                f"Not identical: description <{repr(self.description)}> != "
                f"<{repr(other.description)}>"
            )
        else:
            return True
        return False

    def _repr_kw(self):
        return dict(
            cls=self.__class__.__name__,
            id=self.id,
            name=f": {self.name}" if len(self.name.localizations) else "",
        )

    def __repr__(self):
        return "<{cls} {id}{name}>".format(**self._repr_kw())


class VersionableArtefact(NameableArtefact):
    #: A version string following an agreed convention.
    version: Optional[str] = None
    #: Date from which the version is valid.
    valid_from: Optional[str] = None
    #: Date from which the version is superseded.
    valid_to: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            if self.version and self.version != self.urn_group["version"]:
                raise ValueError(
                    f"Version {self.version} does not match URN {self.urn}"
                )
            else:
                self.version = self.urn_group["version"]
        except KeyError:
            pass

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two VersionableArtefacts are the same if:

        - :meth:`.NameableArtefact.compare` is :obj:`True`, and
        - they have the same :attr:`version`.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare` and :meth:`.NameableArtefact.compare`.
        """
        return super().compare(other, strict) and compare(
            "version", self, other, strict
        )

    def _repr_kw(self) -> Mapping:
        return ChainMap(
            super()._repr_kw(),
            dict(version=f"({self.version})" if self.version else ""),
        )


class MaintainableArtefact(VersionableArtefact):
    #: True if the object is final; otherwise it is in a draft state.
    is_final: Optional[bool] = None
    #: :obj:`True` if the content of the object is held externally; i.e., not
    #: the current :class:`Message`.
    is_external_reference: Optional[bool] = None
    #: URL of an SDMX-compliant web service from which the object can be
    #: retrieved.
    service_url: Optional[str] = None
    #: URL of an SDMX-ML document containing the object.
    structure_url: Optional[str] = None
    #: Association to the Agency responsible for maintaining the object.
    maintainer: Optional["Agency"] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            if self.maintainer and self.maintainer.id != self.urn_group["agency"]:
                raise ValueError(
                    f"Maintainer {self.maintainer} does not match URN {self.urn}"
                )
            else:
                self.maintainer = Agency(id=self.urn_group["agency"])
        except KeyError:
            pass

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two MaintainableArtefacts are the same if:

        - :meth:`.VersionableArtefact.compare` is :obj:`True`, and
        - they have the same :attr:`maintainer`.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare` and :meth:`.VersionableArtefact.compare`.
        """
        return super().compare(other, strict) and compare(
            "maintainer", self, other, strict
        )

    def _repr_kw(self):
        return ChainMap(
            super()._repr_kw(),
            dict(maint=f"{self.maintainer}:" if self.maintainer else ""),
        )

    def __repr__(self):
        return "<{cls} {maint}{id}{version}{name}>".format(**self._repr_kw())


# §3.4: Data Types

ActionType = Enum("ActionType", "delete replace append information")

UsageStatus = Enum("UsageStatus", "mandatory conditional")

# NB three diagrams in the spec show this enumeration containing 'gregorianYearMonth'
#    but not 'gregorianYear' or 'gregorianMonth'. The table in §3.6.3.3 Representation
#    Constructs does the opposite. One ESTAT query (via SGR) shows a real-world usage
#    of 'gregorianYear'; while one query shows usage of 'gregorianYearMonth'; so all
#    three are included.
FacetValueType = Enum(
    "FacetValueType",
    """string bigInteger integer long short decimal float double boolean uri count
    inclusiveValueRange alpha alphaNumeric numeric exclusiveValueRange incremental
    observationalTimePeriod standardTimePeriod basicTimePeriod gregorianTimePeriod
    gregorianYear gregorianMonth gregorianYearMonth gregorianDay reportingTimePeriod
    reportingYear reportingSemester reportingTrimester reportingQuarter reportingMonth
    reportingWeek reportingDay dateTime timesRange month monthDay day time duration
    keyValues identifiableReference dataSetReference""",
)

ConstraintRoleType = Enum("ConstraintRoleType", "allowable actual")


# §3.5: Item Scheme

IT = TypeVar("IT", bound="Item")


class Item(NameableArtefact, Generic[IT]):
    parent: Optional[Union[IT, "ItemScheme"]] = None
    child: List[IT] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add this Item as a child of its parent
        parent = kwargs.get("parent", None)
        if parent:
            parent.append_child(self)

        # Add this Item as a parent of its children
        for c in kwargs.get("child", []):
            self.append_child(c)

    def __contains__(self, item):
        """Recursive containment."""
        for c in self.child:
            if item == c or item in c:
                return True

    def __iter__(self, recurse=True):
        yield self
        for c in self.child:
            yield from iter(c)

    @property
    def hierarchical_id(self):
        """Construct the ID of an Item in a hierarchical ItemScheme.

        Returns, for example, 'A.B.C' for an Item with id 'C' that is the child of an
        item with id 'B', which is the child of a root Item with id 'A'.

        See also
        --------
        .ItemScheme.get_hierarchical
        """
        return (
            f"{self.parent.hierarchical_id}.{self.id}"
            if isinstance(self.parent, self.__class__)
            else self.id
        )

    def append_child(self, other: IT):
        if other not in self.child:
            self.child.append(other)
        other.parent = self

    def get_child(self, id) -> IT:
        """Return the child with the given *id*."""
        for c in self.child:
            if c.id == id:
                return c
        raise ValueError(id)

    def get_scheme(self):
        """Return the :class:`ItemScheme` to which the Item belongs, if any."""
        try:
            # Recurse
            return self.parent.get_scheme()
        except AttributeError:
            # Either this Item is a top-level Item whose .parent refers to the
            # ItemScheme, or it has no parent
            return self.parent


class ItemScheme(MaintainableArtefact, Generic[IT]):
    """SDMX-IM Item Scheme.

    The IM states that ItemScheme “defines a *set* of :class:`Items <.Item>`…” To
    simplify indexing/retrieval, this implementation uses a :class:`dict` for the
    :attr:`items` attribute, in which the keys are the :attr:`~.IdentifiableArtefact.id`
    of the Item.

    Because this may change in future versions of pandaSDMX, user code should not access
    :attr:`items` directly. Instead, use the :func:`getattr` and indexing features of
    ItemScheme, or the public methods, to access and manipulate Items:

    >>> foo = ItemScheme(id='foo')
    >>> bar = Item(id='bar')
    >>> foo.append(bar)
    >>> foo
    <ItemScheme: 'foo', 1 items>
    >>> (foo.bar is bar) and (foo['bar'] is bar) and (bar in foo)
    True

    """

    # TODO add delete()
    # TODO add sorting capability; perhaps sort when new items are inserted

    is_partial: Optional[bool]

    #: Members of the ItemScheme. Both ItemScheme and Item are abstract classes.
    #: Concrete classes are paired: for example, a :class:`.Codelist` contains
    #: :class:`Codes <.Code>`.
    items: Dict[str, IT] = {}

    # The type of the Items in the ItemScheme. This is necessary because the type hint
    # in the class declaration is static; not meant to be available at runtime.
    _Item: Type = Item

    @validator("items", pre=True)
    def convert_to_dict(cls, v):
        if isinstance(v, dict):
            return v
        return {i.id: i for i in v}

    # Convenience access to items
    def __getattr__(self, name: str) -> IT:
        # Provided to pass test_dsd.py
        try:
            return self.__getitem__(name)
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name: str) -> IT:
        return self.items[name]

    def get_hierarchical(self, id: str) -> IT:
        """Get an Item by its :attr:`~.Item.hierarchical_id`."""
        if "." not in id:
            return self.items[id]
        else:
            for item in self.items.values():
                if item.hierarchical_id == id:
                    return item
        raise KeyError(id)

    def __contains__(self, item: Union[str, IT]) -> bool:
        """Check containment.

        No recursive search on children is performed as these are assumed to be included
        in :attr:`items`. Allow searching by Item or its id attribute.
        """
        if isinstance(item, str):
            return item in self.items
        return item in self.items.values()

    def __iter__(self):
        return iter(self.items.values())

    def extend(self, items: Iterable[IT]):
        """Extend the ItemScheme with members of `items`.

        Parameters
        ----------
        items : iterable of :class:`.Item`
            Elements must be of the same class as :attr:`items`.
        """
        for i in items:
            self.append(i)

    def __len__(self):
        return len(self.items)

    def append(self, item: IT):
        """Add *item* to the ItemScheme.

        Parameters
        ----------
        item : same class as :attr:`items`
            Item to add.
        """
        if item.id in self.items:
            raise ValueError(f"Item with id {repr(item.id)} already exists")
        self.items[item.id] = item
        if item.parent is None:
            item.parent = self

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two ItemSchemes are the same if:

        - :meth:`.MaintainableArtefact.compare` is :obj:`True`, and
        - their :attr:`items` have the same keys, and corresponding
          :class:`Items <Item>` compare equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare` and :meth:`.MaintainableArtefact.compare`.
        """
        if not super().compare(other, strict):
            pass
        elif set(self.items) != set(other.items):
            log.debug(
                f"ItemScheme contents differ: {repr(set(self.items))} != "
                + repr(set(other.items))
            )
        else:
            for id, item in self.items.items():
                if not item.compare(other.items[id], strict):
                    log.debug(f"…for items with id={repr(id)}")
                    return False
            return True

        return False

    def __repr__(self):
        return "<{cls} {maint}{id}{version} ({N} items){name}>".format(
            **self._repr_kw(), N=len(self.items)
        )

    def setdefault(self, obj=None, **kwargs) -> IT:
        """Retrieve the item *name*, or add it with *kwargs* and return it.

        The returned object is a reference to an object in the ItemScheme, and is of the
        appropriate class.
        """
        if obj and len(kwargs):
            raise ValueError(
                "cannot give both *obj* and keyword arguments to setdefault()"
            )

        if not obj:
            # Replace a string 'parent' ID with a reference to the object
            parent = kwargs.pop("parent", None)
            if isinstance(parent, str):
                kwargs["parent"] = self[parent]

            # Instantiate an object of the correct class
            obj = self._Item(**kwargs)

        try:
            # Add the object to the ItemScheme
            self.append(obj)
        except ValueError:
            pass  # Already present

        return obj


Item.update_forward_refs()


# §3.6: Structure


class FacetType(BaseModel):
    class Config:
        extra = "forbid"

    #:
    is_sequence: Optional[bool] = None
    #:
    min_length: Optional[int] = None
    #:
    max_length: Optional[int] = None
    #:
    min_value: Optional[float] = None
    #:
    max_value: Optional[float] = None
    #:
    start_value: Optional[float] = None
    #:
    end_value: Optional[str] = None
    #:
    interval: Optional[float] = None
    #:
    time_interval: Optional[timedelta] = None
    #:
    decimals: Optional[int] = None
    #:
    pattern: Optional[str] = None
    #:
    start_time: Optional[datetime] = None
    #:
    end_time: Optional[datetime] = None


class Facet(BaseModel):
    class Config:
        extra = "forbid"

    #:
    type: FacetType = FacetType()
    #:
    value: Optional[str] = None
    #:
    value_type: Optional[FacetValueType] = None


class Representation(BaseModel):
    class Config:
        extra = "forbid"

    #:
    enumerated: Optional[ItemScheme] = None
    #:
    non_enumerated: List[Facet] = []

    def __repr__(self):
        return "<{}: {}, {}>".format(
            self.__class__.__name__, self.enumerated, self.non_enumerated
        )


# §4.4: Concept Scheme


class ISOConceptReference(BaseModel):
    class Config:
        extra = "forbid"

    #:
    agency: str
    #:
    id: str
    #:
    scheme_id: str


class Concept(Item["Concept"]):
    #:
    core_representation: Optional[Representation] = None
    #:
    iso_concept: Optional[ISOConceptReference] = None


class ConceptScheme(ItemScheme[Concept]):
    _Item = Concept


# §3.3: Basic Inheritance


class Component(IdentifiableArtefact):
    #:
    concept_identity: Optional[Concept] = None
    #:
    local_representation: Optional[Representation] = None

    def __contains__(self, value):
        for repr in [
            self.concept_identity.core_representation,
            self.local_representation,
        ]:
            enum = getattr(repr, "enumerated", None)
            if enum is not None:
                return value in enum
        raise TypeError("membership not defined for non-enumerated representations")


CT = TypeVar("CT", bound=Component)


class ComponentList(IdentifiableArtefact, Generic[CT]):
    #:
    components: List[CT] = []
    #:
    auto_order = 1

    # The default type of the Components in the ComponentList. See comment on
    # ItemScheme._Item
    _Component: Type = Component

    # Convenience access to the components
    def append(self, value: CT):
        """Append *value* to :attr:`components`."""
        self.components.append(value)

    def get(self, id) -> CT:
        """Return the component with the given *id*."""
        # Search for an existing Component
        for c in self.components:
            if c.id == id:
                return c
        raise KeyError(id)

    def getdefault(self, id, cls=None, **kwargs) -> CT:
        """Return or create the component with the given *id*.

        If the component is automatically created, its :attr:`.Dimension.order`
        attribute is set to the value of :attr:`auto_order`, which is then incremented.

        Parameters
        ----------
        id : str
            Component ID.
        cls : type, optional
            Hint for the class of a new object.
        kwargs
            Passed to the constructor of :class:`.Component`, or a Component subclass if
            :attr:`.components` is overridden in a subclass of ComponentList.
        """
        try:
            return self.get(id)
        except KeyError:
            # No match
            pass

        # Create a new object of a class:
        # 1. Given by the cls argument,
        # 2. Specified by a subclass' _default_type attribute, or
        # 3. Hinted for a subclass' components attribute.
        cls = cls or self._Component
        component = cls(id=id, **kwargs)

        if "order" not in kwargs:
            # For automatically created dimensions, give a serial value to the
            # order property
            try:
                component.order = self.auto_order
                self.auto_order += 1
            except ValueError:
                pass

        self.components.append(component)
        return component

    # Properties of components
    def __getitem__(self, key) -> CT:
        """Convenience access to components."""
        return self.components[key]

    def __len__(self):
        return len(self.components)

    def __iter__(self):
        return iter(self.components)

    def __repr__(self):
        return "<{}: {}>".format(
            self.__class__.__name__, "; ".join(map(repr, self.components))
        )

    def __eq__(self, other):
        """ID equal and same components occur in same order."""
        return super().__eq__(other) and all(
            s == o for s, o in zip(self.components, other.components)
        )

    # Must be reset because __eq__ is defined
    def __hash__(self):
        return super().__hash__()

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two ComponentLists are the same if:

        - :meth:`.IdentifiableArtefact.compare` is :obj:`True`, and
        - corresponding :attr:`components` compare equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare` and :meth:`.IdentifiableArtefact.compare`.
        """
        return super().compare(other, strict) and all(
            c.compare(other.get(c.id), strict) for c in self.components
        )


# §4.3: Codelist


class Code(Item["Code"]):
    """SDMX-IM Code."""


class Codelist(ItemScheme[Code]):
    _Item = Code


# §4.5: Category Scheme


class Category(Item["Category"]):
    """SDMX-IM Category."""


class CategoryScheme(ItemScheme[Category]):
    _Item = Category


class Categorisation(MaintainableArtefact):
    #:
    category: Optional[Category] = None
    #:
    artefact: Optional[IdentifiableArtefact] = None


# §4.6: Organisations


class Contact(BaseModel):
    """Organization contact information.

    IMF is the only known data provider that returns messages with :class:`Contact`
    information. These differ from the IM in several ways. This class reflects these
    differences:

    - 'name' and 'org_unit' are InternationalString, instead of strings.
    - 'email' may be a list of e-mail addresses, rather than a single address.
    - 'uri' may be a list of URIs, rather than a single URI.
    """

    #:
    name: InternationalString = InternationalString()
    #:
    org_unit: InternationalString = InternationalString()
    #:
    telephone: Optional[str] = None
    #:
    responsibility: InternationalString = InternationalString()
    #:
    email: List[str]
    #:
    uri: List[str]


class Organisation(Item["Organisation"]):
    #:
    contact: List[Contact] = []


class Agency(Organisation):
    pass


# DataProvider delayed until after ConstrainableArtefact, below


# Update forward references to 'Agency'
for cls in list(locals().values()):
    if isclass(cls) and issubclass(cls, MaintainableArtefact):
        cls.update_forward_refs()


class OrganisationScheme:
    """SDMX-IM abstract OrganisationScheme."""


class AgencyScheme(ItemScheme[Agency], OrganisationScheme):
    _Item = Agency


# DataProviderScheme delayed until after DataProvider, below


# §10.2: Constraint inheritance


class ConstrainableArtefact(BaseModel):
    """SDMX-IM ConstrainableArtefact."""


class DataConsumer(Organisation, ConstrainableArtefact):
    """SDMX-IM DataConsumer."""


class DataProvider(Organisation, ConstrainableArtefact):
    """SDMX-IM DataProvider."""


class DataConsumerScheme(ItemScheme[DataConsumer], OrganisationScheme):
    _Item = DataConsumer


class DataProviderScheme(ItemScheme[DataProvider], OrganisationScheme):
    _Item = DataProvider


# §10.3: Constraints


class ConstraintRole(BaseModel):
    #:
    role: ConstraintRoleType


class ComponentValue(BaseModel):
    #:
    value_for: Component
    #:
    value: Any


class DataKey(BaseModel):
    #: :obj:`True` if the :attr:`keys` are included in the :class:`.Constraint`;
    # :obj:`False` if they are excluded.
    included: bool
    #: Mapping from :class:`.Component` to :class:`.ComponentValue` comprising the key.
    key_value: Dict[Component, ComponentValue]


class DataKeySet(BaseModel):
    #: :obj:`True` if the :attr:`keys` are included in the :class:`.Constraint`;
    #: :obj:`False` if they are excluded.
    included: bool
    #: :class:`DataKeys <.DataKey>` appearing in the set.
    keys: List[DataKey] = []

    def __len__(self):
        """:func:`len` of the DataKeySet = :func:`len` of its :attr:`keys`."""
        return len(self.keys)

    def __contains__(self, item):
        return any(item == dk for dk in self.keys)


class Constraint(MaintainableArtefact):
    #: :class:`.DataKeySet` included in the Constraint.
    data_content_keys: Optional[DataKeySet] = None
    # metadata_content_keys: MetadataKeySet = None
    # NB the spec gives 1..* for this attribute, but this implementation allows only 1
    role: ConstraintRole

    # NB this is required to prevent “unhashable type: 'dict'” in pydantic
    class Config:
        validate_assignment = False

    def __contains__(self, value):
        if self.data_content_keys is None:
            raise NotImplementedError("Constraint does not contain a DataKeySet")

        return value in self.data_content_keys


class SelectionValue(BaseModel):
    """SDMX-IM SelectionValue."""


class MemberValue(SelectionValue):
    #:
    value: str
    #:
    cascade_values: Optional[bool] = None

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == (other.value if isinstance(other, KeyValue) else other)

    def __repr__(self):
        return f"{repr(self.value)}" + (" + children" if self.cascade_values else "")


class TimeRangeValue(SelectionValue):
    """SDMX-IM TimeRangeValue."""


class Period(BaseModel):
    is_inclusive: bool
    period: datetime


class RangePeriod(TimeRangeValue):
    start: Period
    end: Period


class MemberSelection(BaseModel):
    #:
    included: bool = True
    #:
    values_for: Component
    #: Value(s) included in the selection. Note that the name of this attribute is not
    #: stated in the IM, so 'values' is chosen for the implementation in this package.
    values: List[SelectionValue] = []

    def __contains__(self, value):
        """Compare KeyValue to MemberValue."""
        return any(mv == value for mv in self.values) is self.included

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} {self.values_for.id} "
            f"{'not ' if not self.included else ''}in {{"
            f"{', '.join(map(repr, self.values))}}}>"
        )


# NB CubeRegion and ContentConstraint are moved below, after Dimension, since CubeRegion
#   references that class.


class AttachmentConstraint(Constraint):
    #:
    attachment: Set[ConstrainableArtefact] = set()


# §5.2: Data Structure Definition


class DimensionComponent(Component):
    #:
    order: Optional[int] = None


class Dimension(DimensionComponent):
    """SDMX-IM Dimension."""


# (continued from §10.3)
class CubeRegion(BaseModel):
    #:
    included: bool = True
    #:
    member: Dict[Dimension, MemberSelection] = {}

    def __contains__(self, other: Union["Key", "KeyValue"]) -> bool:
        """Membership test.

        `other` may be either:

        - :class:`.Key` —all its :class:`.KeyValue` are checked.
        - :class:`.KeyValue` —only the one :class:`.Dimension` for which `other` is a
          value is checked

        Returns
        -------
        bool
            :obj:`True` if:

            - :attr:`.included` *and* `other` is in the CubeRegion;
            - if :attr:`.included` is :obj:`False` *and* `other` is outside the
              CubeRegion; or
            - the `other` is KeyValue referencing a Dimension that is not included in
              :attr:`.member`.
        """
        if isinstance(other, Key):
            result = all(other[ms.values_for.id] in ms for ms in self.member.values())
        elif other.value_for is None:
            # No Dimension reference to use
            result = False
        elif other.value_for not in self.member or len(self.member) > 1:
            # This CubeRegion doesn't have a MemberSelection for the KeyValue's
            # Component; or it concerns additional Components, so inclusion can't be
            # determined
            return True
        else:
            # Check whether the KeyValue is in the indicated dimension
            result = other.value in self.member[other.value_for]

        # Return the correct sense
        return result is self.included

    def to_query_string(self, structure):
        all_values = []

        for dim in structure.dimensions:
            if isinstance(dim, TimeDimension):
                # TimeDimensions handled by query parameters
                continue
            ms = self.member.get(dim, None)
            values = sorted(mv.value for mv in ms.values) if ms else []
            all_values.append("+".join(values))

        return ".".join(all_values)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} {'in' if self.included else 'ex'}clude "
            f"{' '.join(map(repr, self.member.values()))}>"
        )


# (continued from §10.3)
class ContentConstraint(Constraint):
    #: :class:`CubeRegions <.CubeRegion>` included in the ContentConstraint.
    data_content_region: List[CubeRegion] = []
    #:
    content: Set[ConstrainableArtefact] = set()
    # metadata_content_region: MetadataTargetRegion = None

    def __contains__(self, value):
        if self.data_content_region:
            return all(value in cr for cr in self.data_content_region)
        else:
            raise NotImplementedError(
                "ContentConstraint does not contain a CubeRegion."
            )

    def to_query_string(self, structure):
        cr_count = len(self.data_content_region)
        try:
            if cr_count > 1:
                warn(f"to_query_string() using first of {cr_count} " "CubeRegions.")

            return self.data_content_region[0].to_query_string(structure)
        except IndexError:
            raise RuntimeError("ContentConstraint does not contain a CubeRegion.")

    def iter_keys(
        self,
        obj: Union["DataStructureDefinition", "DataflowDefinition"],
        dims: List[str] = [],
    ) -> Generator["Key", None, None]:
        """Iterate over keys.

        A warning is logged if `obj` is not already explicitly associated to this
        ContentConstraint, i.e. present in :attr:`.content`.

        See also
        --------
        .DataStructureDefinition.iter_keys
        """
        if obj not in self.content:
            log.warning(f"{repr(obj)} is not in {repr(self)}.content")

        yield from obj.iter_keys(constraint=self, dims=dims)


class TimeDimension(DimensionComponent):
    """SDMX-IM TimeDimension."""


class MeasureDimension(DimensionComponent):
    """SDMX-IM MeasureDimension."""


class PrimaryMeasure(Component):
    """SDMX-IM PrimaryMeasure."""


class MeasureDescriptor(ComponentList[PrimaryMeasure]):
    _Component = PrimaryMeasure


class AttributeRelationship(BaseModel):
    pass


class _NoSpecifiedRelationship(AttributeRelationship):
    pass


NoSpecifiedRelationship = _NoSpecifiedRelationship()


class _PrimaryMeasureRelationship(AttributeRelationship):
    pass


PrimaryMeasureRelationship = _PrimaryMeasureRelationship()


class DimensionRelationship(AttributeRelationship):
    #:
    dimensions: List[DimensionComponent] = []
    #: NB the IM says "0..*" here in a diagram, but the text does not match.
    group_key: Optional["GroupDimensionDescriptor"] = None


class GroupRelationship(AttributeRelationship):
    # 'Retained for compatibility reasons' in SDMX 2.1; not used by pandaSDMX.
    #:
    group_key: Optional["GroupDimensionDescriptor"] = None


class DataAttribute(Component):
    #:
    related_to: Optional[AttributeRelationship] = None
    #:
    usage_status: Optional[UsageStatus] = None


class ReportingYearStartDay(DataAttribute):
    pass


class AttributeDescriptor(ComponentList[DataAttribute]):
    _Component = DataAttribute


class Structure(MaintainableArtefact):
    #:
    grouping: Optional[ComponentList] = None


class StructureUsage(MaintainableArtefact):
    #:
    structure: Optional[Structure] = None


class DimensionDescriptor(ComponentList[DimensionComponent]):
    """Describes a set of dimensions.

    IM: “An ordered set of metadata concepts that, combined, classify a statistical
    series, and whose values, when combined (the key) in an instance such as a data set,
    uniquely identify a specific observation.”

    :attr:`.components` is a :class:`list` (ordered) of :class:`Dimension`,
    :class:`MeasureDimension`, and/or :class:`TimeDimension`.
    """

    _Component = Dimension

    def assign_order(self):
        """Assign the :attr:`.DimensionComponent.order` attribute.

        The Dimensions in :attr:`components` are numbered, starting from 1.
        """
        for i, component in enumerate(self.components):
            component.order = i + 1

    def order_key(self, key):
        """Return a key ordered according to the DSD."""
        result = key.__class__()
        for dim in sorted(self.components, key=attrgetter("order")):
            try:
                result[dim.id] = key[dim.id]
            except KeyError:
                continue
        return result

    @classmethod
    def from_key(cls, key):
        """Create a new DimensionDescriptor from a *key*.

        For each :class:`KeyValue` in the *key*:

        - A new :class:`Dimension` is created.
        - A new :class:`Codelist` is created, containing the
          :attr:`KeyValue.value`.

        Parameters
        ----------
        key : :class:`Key` or :class:`GroupKey` or :class:`SeriesKey`
        """
        dd = cls()
        for order, (id, kv) in enumerate(key.values.items()):
            cl = Codelist(id=id)
            cl.append(Code(id=kv.value))
            dd.components.append(
                Dimension(
                    id=id,
                    local_representation=Representation(enumerated=cl),
                    order=order,
                )
            )
        return dd


class GroupDimensionDescriptor(DimensionDescriptor):
    #:
    attachment_constraint: Optional[bool] = None
    #:
    constraint: Optional[AttachmentConstraint] = None

    def assign_order(self):
        """:meth:`assign_order` has no effect for GroupDimensionDescriptor."""
        pass


DimensionRelationship.update_forward_refs()
GroupRelationship.update_forward_refs()


class _NullConstraintClass:
    """Constraint that allows anything."""

    def __contains__(self, value):
        return True


_NullConstraint = _NullConstraintClass()


@validate_dictlike
class DataStructureDefinition(Structure, ConstrainableArtefact):
    """SDMX-IM DataStructureDefinition (‘DSD’)."""

    #: A :class:`AttributeDescriptor` that describes the attributes of the data
    #: structure.
    attributes: AttributeDescriptor = AttributeDescriptor()
    #: A :class:`DimensionDescriptor` that describes the dimensions of the data
    #: structure.
    dimensions: DimensionDescriptor = DimensionDescriptor()
    #: A :class:`.MeasureDescriptor`.
    measures: MeasureDescriptor = MeasureDescriptor()
    #: Mapping from  :attr:`.GroupDimensionDescriptor.id` to
    #: :class:`.GroupDimensionDescriptor`.
    group_dimensions: DictLike[str, GroupDimensionDescriptor] = dictlike_field()

    # Convenience methods
    def iter_keys(
        self, constraint: Constraint = None, dims: List[str] = []
    ) -> Generator["Key", None, None]:
        """Iterate over keys.

        Parameters
        ----------
        constraint : Constraint, optional
            If given, only yield Keys that are within the constraint.
        dims : list of str, optional
            If given, only iterate over allowable values for the Dimensions with these
            IDs. Other dimensions have only a single value like "(DIM_ID)", where
            DIM_ID is the ID of the dimension.
        """
        # NB for performance, the implementation tries to use iterators and avoid
        #    constructing full-length tuples/lists at any point

        _constraint = constraint or _NullConstraint
        dims = dims or [dim.id for dim in self.dimensions.components]

        # Utility to return an immutable function that produces KeyValues. The
        # arguments are frozen so these can be set using loop variables and stored in a
        # map() object that isn't modified on future loops
        def make_factory(id=None, value_for=None):
            return lambda value: KeyValue.construct(
                id=id, value=value, value_for=value_for
            )

        # List of iterables of (dim.id, KeyValues) along each dimension
        all_kvs: List[Iterable[Tuple[str, KeyValue]]] = []

        # Iterate over dimensions
        for dim in self.dimensions.components:
            if (
                dim.id not in dims
                or dim.local_representation is None
                or dim.local_representation.enumerated is None
            ):
                # `dim` is not enumerated by an ItemScheme, or not included in the
                # `dims` argument and not to be iterated over. Create a placeholder.
                all_kvs.append(
                    [(dim.id, KeyValue(id=dim.id, value=f"({dim.id})", value_for=dim))]
                )
            else:
                # Create a KeyValue for each Item in the ItemScheme; filter through any
                # constraint.
                all_kvs.append(
                    map(
                        lambda kv: (kv.id, kv),
                        filter(
                            _constraint.__contains__,
                            map(
                                make_factory(id=dim.id, value_for=dim),
                                dim.local_representation.enumerated,
                            ),
                        ),
                    )
                )

        # Create Key objects from Cartesian product of KeyValues along each dimension
        # NB this does not work with DataKeySet
        # TODO improve to work with DataKeySet
        yield from filter(_constraint.__contains__, map(Key._fast, product(*all_kvs)))

    def make_constraint(self, key):
        """Return a constraint for `key`.

        `key` is a :class:`dict` wherein:

        - keys are :class:`str` ids of Dimensions appearing in this DSD's
          :attr:`dimensions`, and
        - values are '+'-delimited :class:`str` containing allowable values, *or*
          iterables of :class:`str`, each an allowable value.

        For example::

            cc2 = dsd.make_constraint({'foo': 'bar+baz', 'qux': 'q1+q2+q3'})

        ``cc2`` includes any key where the 'foo' dimension is 'bar' *or* 'baz', *and*
        the 'qux' dimension is one of 'q1', 'q2', or 'q3'.

        Returns
        -------
        ContentConstraint
            A constraint with one :class:`CubeRegion` in its
            :attr:`data_content_region <ContentConstraint.data_content_region>` ,
            including only the values appearing in `key`.

        Raises
        ------
        ValueError
            if `key` contains a dimension IDs not appearing in :attr:`dimensions`.
        """
        # Make a copy to avoid pop()'ing off the object in the calling scope
        key = key.copy()

        cr = CubeRegion()
        for dim in self.dimensions:
            mvs = set()
            try:
                values = key.pop(dim.id)
            except KeyError:
                continue

            values = values.split("+") if isinstance(values, str) else values
            for value in values:
                # TODO validate values
                mvs.add(MemberValue(value=value))

            cr.member[dim] = MemberSelection(included=True, values_for=dim, values=mvs)

        if len(key):
            raise ValueError(
                "Dimensions {!r} not in {!r}".format(list(key.keys()), self.dimensions)
            )

        return ContentConstraint(
            data_content_region=[cr],
            role=ConstraintRole(role=ConstraintRoleType.allowable),
        )

    @classmethod
    def from_keys(cls, keys):
        """Return a new DSD given some *keys*.

        The DSD's :attr:`dimensions` refers to a set of new :class:`Concepts <Concept>`
        and :class:`Codelists <Codelist>`, created to represent all the values observed
        across *keys* for each dimension.

        Parameters
        ----------
        keys : iterable of :class:`Key`
            or of subclasses such as :class:`SeriesKey` or :class:`GroupKey`.
        """
        iter_keys = iter(keys)
        dd = DimensionDescriptor.from_key(next(iter_keys))

        for k in iter_keys:
            for i, (id, kv) in enumerate(k.values.items()):
                try:
                    dd[i].local_representation.enumerated.append(Code(id=kv.value))
                except ValueError:
                    pass  # Item already exists

        return cls(dimensions=dd)

    def make_key(self, key_cls, values: Mapping, extend=False, group_id=None):
        """Make a :class:`.Key` or subclass.

        Parameters
        ----------
        key_cls : Key or SeriesKey or GroupKey
            Class of Key to create.
        values : dict
            Used to construct :attr:`.Key.values`.
        extend : bool, optional
            If :obj:`True`, make_key will not return :class:`KeyError` on missing
            dimensions. Instead :attr:`dimensions` (`key_cls` is Key or SeriesKey) or
            :attr:`group_dimensions` (`key_cls` is GroupKey) will be extended by
            creating new Dimension objects.
        group_id : str, optional
            When `key_cls` is :class`.GroupKey`, the ID of the
            :class:`.GroupDimensionDescriptor` that structures the key.

        Returns
        -------
        Key
            An instance of `key_cls`.

        Raises
        ------
        KeyError
            If any of the keys of `values` is not a Dimension or Attribute in the DSD.
        """
        # Methods to get dimensions and attributes
        get_method = "getdefault" if extend else "get"
        dim = getattr(self.dimensions, get_method)
        attr = getattr(self.attributes, get_method)

        # Arguments for creating the Key
        args: Dict[str, Any] = dict(described_by=self.dimensions)

        if key_cls is GroupKey:
            # Get the GroupDimensionDescriptor, if indicated by group_id
            gdd = self.group_dimensions.get(group_id, None)

            if group_id and not gdd and not extend:
                # Cannot create
                raise KeyError(group_id)
            elif group_id and extend:
                # Create the GDD
                gdd = GroupDimensionDescriptor(id=group_id)
                self.group_dimensions[gdd.id] = gdd

                # GroupKey will have same ID and be described by the GDD
                args = dict(id=group_id, described_by=gdd)

                # Dimensions to be retrieved from the GDD
                def dim(id):
                    # Get from the DimensionDescriptor
                    new_dim = self.dimensions.getdefault(id)
                    # Add to the GDD
                    gdd.components.append(new_dim)
                    return gdd.get(id)

            else:
                # Not described by anything
                args = dict()

        key = key_cls(**args)

        # Convert keyword arguments to either KeyValue or AttributeValue
        keyvalues = []
        for order, (id, value) in enumerate(values.items()):
            args = dict(id=id, value=value)

            if id in self.attributes:
                # Reference a DataAttribute from the AttributeDescriptor
                da = attr(id)
                # Store the attribute value, referencing
                key.attrib[da.id] = AttributeValue(**args, value_for=da)
                continue

            # Reference a Dimension from the DimensionDescriptor. If extend=False and
            # the Dimension does not exist, this will raise KeyError
            args["value_for"] = dim(id)

            # Retrieve the order
            order = args["value_for"].order

            # Store a KeyValue, to be sorted later
            keyvalues.append((order, KeyValue(**args)))

        # Sort the values according to *order*
        key.values.update({kv.id: kv for _, kv in sorted(keyvalues)})

        return key

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two DataStructureDefinitions are the same if each of :attr:`attributes`,
        :attr:`dimensions`, :attr:`measures`, and :attr:`group_dimensions` compares
        equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :meth:`.ComponentList.compare`.
        """
        return all(
            getattr(self, attr).compare(getattr(other, attr), strict)
            for attr in ("attributes", "dimensions", "measures", "group_dimensions")
        )


class DataflowDefinition(StructureUsage, ConstrainableArtefact):
    #:
    structure: DataStructureDefinition = DataStructureDefinition()

    def iter_keys(
        self, constraint: Constraint = None, dims: List[str] = []
    ) -> Generator["Key", None, None]:
        """Iterate over keys.

        See also
        --------
        .DataStructureDefinition.iter_keys
        """
        yield from self.structure.iter_keys(constraint=constraint, dims=dims)


# §5.4: Data Set


def value_for_dsd_ref(kind, args, kwargs):
    """Maybe replace a string 'value_for' in *kwargs* with a DSD reference."""
    try:
        dsd = kwargs.pop("dsd")
        descriptor = getattr(dsd, kind + "s")
        kwargs["value_for"] = descriptor.get(kwargs["value_for"])
    except KeyError:
        pass
    return args, kwargs


class KeyValue(BaseModel):
    """One value in a multi-dimensional :class:`Key`."""

    #:
    id: str
    #: The actual value.
    value: Any
    #:
    value_for: Optional[Dimension] = None

    def __init__(self, *args, **kwargs):
        args, kwargs = value_for_dsd_ref("dimension", args, kwargs)
        super().__init__(*args, **kwargs)

    def __eq__(self, other):
        """Compare the value to a simple Python built-in type or other key-like.

        `other` may be :class:`.KeyValue` or :class:`.ComponentValue`; if so, and both
        `self` and `other` have :attr:`.value_for`, these must refer to the same object.
        """
        if isinstance(other, (KeyValue, ComponentValue)):
            return (self.value == other.value) and (
                self.value_for in (None, other.value_for) or other.value_for is None
            )
        elif isinstance(other, MemberValue):
            return self.value == other.value
        else:
            return self.value == other

    def __str__(self):
        return "{0.id}={0.value}".format(self)

    def __repr__(self):
        return "<{0.__class__.__name__}: {0.id}={0.value}>".format(self)

    def __hash__(self):
        # KeyValue instances with the same id & value hash identically
        return hash(self.id + str(self.value))


TimeKeyValue = KeyValue


class AttributeValue(BaseModel):
    """SDMX-IM AttributeValue.

    In the spec, AttributeValue is an abstract class. Here, it serves as both the
    concrete subclasses CodedAttributeValue and UncodedAttributeValue.
    """

    # TODO separate and enforce properties of Coded- and UncodedAttributeValue
    #:
    value: Union[str, Code]
    #:
    value_for: Optional[DataAttribute] = None
    #:
    start_date: Optional[date] = None

    def __init__(self, *args, **kwargs):
        args, kwargs = value_for_dsd_ref("attribute", args, kwargs)
        super(AttributeValue, self).__init__(*args, **kwargs)

    def __eq__(self, other):
        """Compare the value to a Python built-in type, e.g. str."""
        return self.value == other

    def __str__(self):
        # self.value directly for UncodedAttributeValue
        return self.value if isinstance(self.value, str) else self.value.id

    def __repr__(self):
        return "<{}: {}={}>".format(self.__class__.__name__, self.value_for, self.value)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two AttributeValues are equal if their properties are equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return all(
            compare(attr, self, other, strict)
            for attr in ["start_date", "value", "value_for"]
        )


@validate_dictlike
class Key(BaseModel):
    """SDMX Key class.

    The constructor takes an optional list of keyword arguments; the keywords are used
    as Dimension or Attribute IDs, and the values as KeyValues.

    For convience, the values of the key may be accessed directly:

    >>> k = Key(foo=1, bar=2)
    >>> k.values['foo']
    1
    >>> k['foo']
    1

    Parameters
    ----------
    dsd : DataStructureDefinition
        If supplied, the :attr:`~.DataStructureDefinition.dimensions` and
        :attr:`~.DataStructureDefinition.attributes` are used to separate the `kwargs`
        into :class:`KeyValues <.KeyValue>` and
        :class:`AttributeValues <.AttributeValue>`. The `kwargs` for
        :attr:`described_by`, if any, must be
        :attr:`~.DataStructureDefinition.dimensions` or appear in
        :attr:`~.DataStructureDefinition.group_dimensions`.
    kwargs
        Dimension and Attribute IDs, and/or the class properties.

    """

    #:
    attrib: DictLike[str, AttributeValue] = dictlike_field()
    #:
    described_by: Optional[DimensionDescriptor] = None
    #: Individual KeyValues that describe the key.
    values: DictLike[str, KeyValue] = dictlike_field()

    def __init__(self, arg: Union[Mapping, Sequence[KeyValue]] = None, **kwargs):
        # DimensionDescriptor
        dd = kwargs.pop("described_by", None)

        super().__init__(
            attrib=kwargs.pop("attrib", DictLike()), described_by=dd, values=DictLike()
        )

        if arg and isinstance(arg, Mapping):
            if len(kwargs):
                raise ValueError(
                    "Key() accepts either a single argument, or keyword arguments; not "
                    "both."
                )
            kwargs.update(arg)

        if isinstance(arg, Sequence):
            # Sequence of already-prepared KeyValues; assume already sorted
            kvs: Iterable[Tuple] = map(lambda kv: (kv.id, kv), arg)
        else:
            # Convert bare keyword arguments to KeyValue
            kvs = []
            for order, (id, value) in enumerate(kwargs.items()):
                args = dict(id=id, value=value)
                if dd:
                    # Reference the Dimension
                    args["value_for"] = dd.get(id)
                    # Use the existing Dimension's order attribute
                    order = args["value_for"].order

                # Store a KeyValue, to be sorted later
                kvs.append((order, (id, KeyValue(**args))))

            # Sort the values according to *order*, then unwrap
            kvs = map(itemgetter(1), sorted(kvs))

        for id, kv in kvs:
            self.values[id] = kv

    @classmethod
    def _fast(cls, kvs):
        """Use :meth:`pydantic.BaseModel.construct` for faster construction."""
        return cls.construct(values=DictLike(kvs))

    def __len__(self):
        """The length of the Key is the number of KeyValues it contains."""
        return len(self.values)

    def __contains__(self, other):
        """A Key contains another if it is a superset."""
        try:
            return all([self.values[k] == v for k, v in other.values.items()])
        except KeyError:
            # 'k' in other does not appear in this Key()
            return False

    def __iter__(self):
        yield from self.values.values()

    # Convenience access to values by name
    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):
        # Convert a bare string or other Python object to a KeyValue instance
        if not isinstance(value, KeyValue):
            value = KeyValue(id=name, value=value)
        self.values[name] = value

    # Convenience access to values by attribute
    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError as e:
            raise AttributeError(e)

    # Copying
    def __copy__(self):
        result = Key()
        if self.described_by:
            result.described_by = self.described_by
        for kv in self.values.values():
            result[kv.id] = kv
        return result

    def copy(self, arg=None, **kwargs):
        result = copy(self)
        for id, value in kwargs.items():
            result[id] = value
        return result

    def __add__(self, other):
        if not isinstance(other, Key):
            raise NotImplementedError
        result = copy(self)
        for id, value in other.values.items():
            result[id] = value
        return result

    def __radd__(self, other):
        if other is None:
            return copy(self)
        else:
            raise NotImplementedError

    def __eq__(self, other):
        if hasattr(other, "values"):
            # Key
            return all(
                [a == b for a, b in zip(self.values.values(), other.values.values())]
            )
        elif hasattr(other, "key_value"):
            # DataKey
            return all(
                [a == b for a, b in zip(self.values.values(), other.key_value.values())]
            )
        elif isinstance(other, str) and len(self.values) == 1:
            return self.values[0] == other
        else:
            raise ValueError(other)

    def __hash__(self):
        # Hash of the individual KeyValues, in order
        return hash(tuple(hash(kv) for kv in self.values.values()))

    # Representations

    def __str__(self):
        return "({})".format(", ".join(map(str, self.values.values())))

    def __repr__(self):
        return "<{}: {}>".format(
            self.__class__.__name__, ", ".join(map(str, self.values.values()))
        )

    def order(self, value=None):
        if value is None:
            value = self
        try:
            return self.described_by.order_key(value)
        except AttributeError:
            return value

    def get_values(self):
        return tuple([kv.value for kv in self.values.values()])


class GroupKey(Key):
    #:
    id: Optional[str] = None
    #:
    described_by: Optional[GroupDimensionDescriptor] = None

    def __init__(self, arg: Mapping = None, **kwargs):
        # Remove the 'id' keyword argument
        id = kwargs.pop("id", None)
        super().__init__(arg, **kwargs)
        self.id = id


class SeriesKey(Key):
    #: :mod:`sdmx` extension not in the IM.
    group_keys: Set[GroupKey] = set()

    @property
    def group_attrib(self):
        """Return a view of combined group attributes."""
        # Needed to pass existing tests
        view = DictLike()
        for gk in self.group_keys:
            view.update(gk.attrib)
        return view


@validate_dictlike
class Observation(BaseModel):
    """SDMX-IM Observation.

    This class also implements the spec classes ObservationValue,
    UncodedObservationValue, and CodedObservation.
    """

    #:
    attached_attribute: DictLike[str, AttributeValue] = dictlike_field()
    #:
    series_key: Optional[SeriesKey] = None
    #: Key for dimension(s) varying at the observation level.
    dimension: Optional[Key] = None
    #: Data value.
    value: Optional[Union[Any, Code]] = None
    #:
    value_for: Optional[PrimaryMeasure] = None
    #: :mod:`sdmx` extension not in the IM.
    group_keys: Set[GroupKey] = set()

    @property
    def attrib(self):
        """Return a view of combined observation, series & group attributes."""
        view = self.attached_attribute.copy()
        view.update(getattr(self.series_key, "attrib", {}))
        for gk in self.group_keys:
            view.update(gk.attrib)
        return view

    @property
    def dim(self):
        return self.dimension

    @property
    def key(self):
        """Return the entire key, including KeyValues at the series level."""
        return self.series_key + self.dimension

    def __len__(self):
        # FIXME this is unintuitive; maybe deprecate/remove?
        return len(self.key)

    def __str__(self):
        return "{0.key}: {0.value}".format(self)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two Observations are equal if:

        - their :attr:`dimension`, :attr:`value`, :attr:`series_key`, and
          :attr:`value_for` are all equal,
        - their corresponding :attr:`attached_attribute` and :attr:`group_keys` are all
          equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return (
            all(
                compare(attr, self, other, strict)
                for attr in ["dimension", "series_key", "value", "value_for"]
            )
            and self.attached_attribute.compare(other.attached_attribute)
            and self.group_keys == other.group_keys
        )


@validate_dictlike
class DataSet(AnnotableArtefact):
    # SDMX-IM features
    #:
    action: Optional[ActionType] = None
    #:
    attrib: DictLike[str, AttributeValue] = dictlike_field()
    #:
    valid_from: Optional[str] = None
    #:
    described_by: Optional[DataflowDefinition] = None
    #:
    structured_by: Optional[DataStructureDefinition] = None

    #: All observations in the DataSet.
    obs: List[Observation] = []

    #: Map of series key → list of observations.
    #: :mod:`sdmx` extension not in the IM.
    series: DictLike[SeriesKey, List[Observation]] = dictlike_field()
    #: Map of group key → list of observations.
    #: :mod:`sdmx` extension not in the IM.
    group: DictLike[GroupKey, List[Observation]] = dictlike_field()

    def __len__(self):
        return len(self.obs)

    def _add_group_refs(self, target):
        """Associate *target* with groups in this dataset.

        *target* may be an instance of SeriesKey or Observation.
        """
        for group_key in self.group:
            if group_key in (target if isinstance(target, SeriesKey) else target.key):
                target.group_keys.add(group_key)
                if isinstance(target, Observation):
                    self.group[group_key].append(target)

    def add_obs(self, observations, series_key=None):
        """Add *observations* to a series with *series_key*.

        Checks consistency and adds group associations."""
        if series_key is not None:
            # Associate series_key with any GroupKeys that apply to it
            self._add_group_refs(series_key)
            # Maybe initialize empty series
            self.series.setdefault(series_key, [])

        for obs in observations:
            # Associate the observation with any GroupKeys that contain it
            self._add_group_refs(obs)

            # Store a reference to the observation
            self.obs.append(obs)

            if series_key is not None:
                if obs.series_key is None:
                    # Assign the observation to the SeriesKey
                    obs.series_key = series_key
                else:
                    # Check that the Observation is not associated with a different
                    # SeriesKey
                    assert obs.series_key is series_key

                # Store a reference to the observation
                self.series[series_key].append(obs)

    @validator("action")
    def _validate_action(cls, value):
        if value in ActionType:
            return value
        else:
            return ActionType[value]

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two DataSets are the same if:

        - their :attr:`action`, :attr:`valid_from` compare equal.
        - all dataset-level attached attributes compare equal.
        - they have the same number of observations, series, and groups.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return (
            compare("action", self, other, strict)
            and compare("valid_from", self, other, strict)
            and self.attrib.compare(other.attrib, strict)
            and len(self.obs) == len(other.obs)
            and len(self.series) == len(other.series)
            and len(self.group) == len(other.group)
            and all(o[0].compare(o[1], strict) for o in zip(self.obs, other.obs))
        )


class StructureSpecificDataSet(DataSet):
    """SDMX-IM StructureSpecificDataSet."""


class GenericDataSet(DataSet):
    """SDMX-IM GenericDataSet."""


class GenericTimeSeriesDataSet(DataSet):
    """SDMX-IM GenericTimeSeriesDataSet."""


class StructureSpecificTimeSeriesDataSet(DataSet):
    """SDMX-IM StructureSpecificTimeSeriesDataSet."""


class _AllDimensions:
    pass


AllDimensions = _AllDimensions()


# §11: Data Provisioning


class Datasource(BaseModel):
    url: str


class SimpleDatasource(Datasource):
    pass


class QueryDatasource(Datasource):
    # Abstract.
    # NB the SDMX-IM inconsistently uses this name and 'WebServicesDatasource'.
    pass


class RESTDatasource(QueryDatasource):
    pass


class ProvisionAgreement(MaintainableArtefact, ConstrainableArtefact):
    #:
    structure_usage: Optional[StructureUsage] = None
    #:
    data_provider: Optional[DataProvider] = None


#: The SDMX-IM defines 'packages'; these are used in URNs.
PACKAGE = dict()

_PACKAGE_CLASS: Dict[str, set] = {
    "base": {Agency, AgencyScheme, DataProvider, DataProviderScheme},
    "categoryscheme": {Category, Categorisation, CategoryScheme},
    "codelist": {Code, Codelist},
    "conceptscheme": {Concept, ConceptScheme},
    "datastructure": {DataflowDefinition, DataStructureDefinition, StructureUsage},
    "registry": {ContentConstraint, ProvisionAgreement},
}

for package, classes in _PACKAGE_CLASS.items():
    PACKAGE.update({cls: package for cls in classes})

del cls


@lru_cache()
def get_class(name: Union[str, Resource], package=None) -> Optional[Type]:
    """Return a class for `name` and (optional) `package` names."""
    if isinstance(name, Resource):
        # Convert a Resource enumeration value to a string

        # Expected class name in lower case; maybe just the enumeration value
        match = Resource.class_name(name).lower()

        # Match class names in lower case. If no match or >2, only() returns None, and
        # KeyError occurs below
        name = only(filter(lambda g: g.lower() == match, globals().keys()))

    name = {"Dataflow": "DataflowDefinition"}.get(name, name)

    try:
        cls = globals()[name]
    except KeyError:
        return None

    if package and package != PACKAGE[cls]:
        raise ValueError(f"Package {repr(package)} invalid for {name}")

    return cls


def parent_class(cls):
    """Return the class that contains objects of type `cls`.

    E.g. if `cls` is :class:`.PrimaryMeasure`, returns :class:`.MeasureDescriptor`.
    """
    return {
        Agency: AgencyScheme,
        Category: CategoryScheme,
        Code: Codelist,
        Concept: ConceptScheme,
        Dimension: DimensionDescriptor,
        DataProvider: DataProviderScheme,
        GroupDimensionDescriptor: DataStructureDefinition,
        PrimaryMeasure: MeasureDescriptor,
    }[cls]
