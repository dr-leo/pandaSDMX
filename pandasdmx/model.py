"""SDMX Information Model (SDMX-IM).

This module implements many of the classes described in the SDMX-IM
specification ('spec'), which is available from:

- https://sdmx.org/?page_id=5008
- https://sdmx.org/wp-content/uploads/
    SDMX_2-1-1_SECTION_2_InformationModel_201108.pdf

Details of the implementation:

- Python typing and pydantic are used to enforce the types of attributes
  that reference instances of other classes.
- Some classes have convenience attributes not mentioned in the spec, to ease
  navigation between related objects. These are marked “:mod:`pandaSDMX`
  extension not in the IM.”
- Class definitions are grouped by section of the spec, but these sections
  appear out of order so that dependent classes are defined first.

"""
# TODO:
# - For a complete implementation of the spec:
#   - Enforce TimeKeyValue (instead of KeyValue) for
#     {Generic,StructureSpecific} TimeSeriesDataSet.
# - For convenience:
#   - Guess URNs using the standard format.

from copy import copy
from collections.abc import Collection, Iterable as IterableABC
from datetime import date, datetime, timedelta
from enum import Enum
from inspect import isclass
from operator import attrgetter
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Union,
    )
from warnings import warn

from pandasdmx.util import (
    BaseModel,
    DictLike,
    get_class_hint,
    validate_dictlike,
    )
from pydantic import validator


# TODO read this from the environment, or use any value set in the SDMX XML
# spec. Currently set to 'en' because test_dsd.py expects it
DEFAULT_LOCALE = 'en'


# 3.2: Base structures

class InternationalString:
    """SDMX-IM InternationalString.

    SDMX-IM LocalisedString is not implemented. Instead, the 'localizations' is
    a mapping where:

     - keys correspond to the 'locale' property of LocalisedString.
     - values correspond to the 'label' property of LocalisedString.

    When used as a type hint with pydantic, InternationalString fields can be
    assigned to in one of four ways::

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

    Only the first method preserves existing localizations; the latter three
    replace them.

    """
    localizations: Dict[str, str] = {}

    def __init__(self, value=None, **kwargs):
        super().__init__()

        # Handle initial values according to type
        if isinstance(value, str):
            # Bare string
            value = {DEFAULT_LOCALE: value}
        elif (isinstance(value, Collection) and len(value) == 2
              and isinstance(value[0], str)):
            # 2-tuple of str is (locale, label)
            value = {value[0]: value[1]}
        elif isinstance(value, IterableABC):
            # Iterable of 2-tuples
            value = {locale: label for (locale, label) in value}
        elif value is None:
            # Keyword arguments → dict, possibly empty
            value = dict(kwargs)
        elif isinstance(value, dict):
            # dict; use directly
            pass
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
            return self.__dict__['localizations'][name]
        except KeyError:
            raise AttributeError(name)

    def __add__(self, other):
        result = copy(self)
        result.localizations.update(other.localizations)
        return result

    def localized_default(self, locale):
        """Return the string in *locale*, or else the first defined."""
        try:
            return self.localizations[locale]
        except KeyError:
            if len(self.localizations):
                # No label in the default locale; use the first stored value
                return next(iter(self.localizations.values()))
            else:
                return ''

    def __str__(self):
        return self.localized_default(DEFAULT_LOCALE)

    def __repr__(self):
        return '\n'.join(['{}: {}'.format(*kv) for kv in
                          sorted(self.localizations.items())])

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
    #: Can be used to disambiguate multiple annotations for one
    #: AnnotableArtefact.
    id: str = None
    #: Title, used to identify an annotation.
    title: str = None
    #: Specifies how the annotation is processed.
    type: str = None
    #: A link to external descriptive text.
    url: str = None

    #: Content of the annotation.
    text: InternationalString = InternationalString()


class AnnotableArtefact(BaseModel):
    #: :class:`Annotations <.Annotation>` of the object.
    #:
    #: :mod:`pandaSDMX` implementation: The IM does not specify the name of
    #: this feature.
    annotations: List[Annotation] = []


class IdentifiableArtefact(AnnotableArtefact):
    #: Unique identifier of the object.
    id: str = None
    #: Universal resource identifier that may or may not be resolvable.
    uri: str = None
    #: Universal resource name. For use in SDMX registries; all registered
    #: objects have a URN.
    urn: str = None

    def __eq__(self, other):
        """Equality comparison.

        IdentifiableArtefacts can be compared to other instances. For
        convenience, a string containing the object's ID is also equal to the
        object.
        """
        if isinstance(other, self.__class__):
            return self.id == other.id
        elif isinstance(other, str):
            return self.id == other

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.id if self.id else '<missing id>'

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.id)


class NameableArtefact(IdentifiableArtefact):
    #: Multi-lingual name of the object.
    name: InternationalString = InternationalString()
    #: Multi-lingual description of the object.
    description: InternationalString = InternationalString()

    def __repr__(self):
        return "<{}: '{}'='{}'>".format(
            self.__class__.__name__,
            self.id,
            str(self.name))


class VersionableArtefact(NameableArtefact):
    #: A version string following an agreed convention.
    version: str = None
    #: Date from which the version is valid.
    valid_from: str = None
    #: Date from which the version is superseded.
    valid_to: str = None


class MaintainableArtefact(VersionableArtefact):
    #: True if the object is final; otherwise it is in a draft state.
    is_final: Optional[bool]
    #: :obj:`True` if the content of the object is held externally; i.e., not
    #: the current :class:`Message`.
    is_external_reference: Optional[bool]
    #: URL of an SDMX-compliant web service from which the object can be
    #: retrieved.
    service_url: Optional[str]
    #: URL of an SDMX-ML document containing the object.
    structure_url: Optional[str]
    #: Association to the Agency responsible for maintaining the object.
    maintainer: Optional['Agency']


# 3.4: Data Types

ActionType = Enum('ActionType', 'delete replace append information', type=str)

UsageStatus = Enum('UsageStatus', 'mandatory conditional')

# NB three diagrams in the spec show this enumeration containing
#    'gregorianYearMonth' but not 'gregorianYear' or 'gregorianMonth'. The
#    table in §3.6.3.3 Representation Constructs does the opposite. One ESTAT
#    query (via SGR) shows a real-world usage of 'gregorianYear'; while one NB
#    query shows usage of 'gregorianYearMonth'; so all three are included.
FacetValueType = Enum(
    'FacetValueType',
    """string bigInteger integer long short decimal float double boolean uri
    count inclusiveValueRange alpha alphaNumeric numeric exclusiveValueRange
    incremental observationalTimePeriod standardTimePeriod basicTimePeriod
    gregorianTimePeriod gregorianYear gregorianMonth gregorianYearMonth
    gregorianDay reportingTimePeriod reportingYear reportingSemester
    reportingTrimester reportingQuarter reportingMonth reportingWeek
    reportingDay dateTime timesRange month monthDay day time duration keyValues
    identifiableReference dataSetReference""")

ConstraintRoleType = Enum('ConstraintRoleType', 'allowable actual')


# 3.5: Item Scheme

class Item(NameableArtefact):
    parent: 'Item' = None
    child: List['Item'] = []

    # NB this is required to prevent RecursionError in pydantic;
    #    see https://github.com/samuelcolvin/pydantic/issues/524
    class Config:
        validate_assignment_exclude = 'parent'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add this Item as a child of its parent
        parent = kwargs.get('parent', None)
        if parent and self not in parent.child:
            parent.child.append(self)

        # Add this Item as a parent of its children
        for c in kwargs.get('child', []):
            c.parent = self

    def __contains__(self, item):
        """Recursive containment."""
        for c in self.child:
            if item == c or item in c:
                return True

    def get_child(self, id):
        """Return the child with the given *id*."""
        for c in self.child:
            if c.id == id:
                return c
        raise ValueError(id)


Item.update_forward_refs()


class ItemScheme(MaintainableArtefact):
    """SDMX-IM Item Scheme.

    The IM states that ItemScheme “defines a *set* of :class:`Items <.Item>`…”
    To simplify indexing/retrieval, this implementation uses a :class:`dict`
    for the :attr:`items` attribute, in which the keys are the
    :attr:`~.IdentifiableArtefact.id` of the Item.

    Because this may change in future versions of pandaSDMX, user code should
    not access :attr:`items` directly. Instead, use the :func:`getattr` and
    indexing features of ItemScheme, or the public methods, to access and
    manipulate Items:

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

    # Internal: the type of the Items in the ItemScheme.
    _item_type = Item

    #: Members of the ItemScheme. Both ItemScheme and Item are abstract
    #: classes. Concrete classes are paired: for example, a
    #: :class:`.Codelist` contains :class:`Codes <.Code>`.
    items: Dict[str, _item_type] = {}

    @validator('items', pre=True)
    def convert_to_dict(cls, v):
        if isinstance(v, dict):
            return v
        return {i.id: i for i in v}

    # Convenience access to items
    def __getattr__(self, name):
        # Provided to pass test_dsd.py
        return self.__getitem__(name)

    def __getitem__(self, name):
        return self.items[name]

    def __contains__(self, item: Union[str, _item_type]):
        """Check containment.

        No recursive search on children is performed as these are assumed to be
        included in :attr:`items`. Allow searching by Item or its id
        attribute.
        """
        if isinstance(item, str):
            return item in self.items
        return item in self.items.values()

    def __iter__(self):
        return iter(self.items.values())

    def extend(self, items: Iterable[_item_type]):
        """Extend the ItemScheme with members of *items*.

        Parameters
        ----------
        items : iterable of :class:`.Item`
            Elements must be of the same class as :attr:`items`.
        """
        # TODO enhance to accept an ItemScheme
        self.items.update({i.id: i for i in items})

    def __len__(self):
        return len(self.items)

    def append(self, item: Item):
        """Add *item* to the ItemScheme.

        Parameters
        ----------
        item : same class as :attr:`items`
            Item to add.
        """
        self.items[item.id] = item

    def __repr__(self):
        return "<{}: '{}', {} items>".format(
            self.__class__.__name__,
            self.id,
            len(self.items))

    def setdefault(self, obj=None, **kwargs):
        """Retrieve the item *name*, or add it with *kwargs* and return it.

        The returned object is a reference to an object in the ItemScheme, and
        is of the appropriate class.
        """
        if obj and len(kwargs):
            raise ValueError('cannot give both *obj* and keyword arguments to '
                             'setdefault()')

        if not obj:
            # Replace a string 'parent' ID with a reference to the object
            parent = kwargs.pop('parent', None)
            if isinstance(parent, str):
                kwargs['parent'] = self[parent]

            # Instantiate an object of the correct class
            obj = self._item_type(**kwargs)

        if obj not in self.items.values():
            # Add the object to the ItemScheme
            self.items[obj.id] = obj

        return obj


# 3.6: Structure

class FacetType(BaseModel):
    #:
    is_sequence: Optional[bool]
    #:
    min_length: Optional[int]
    #:
    max_length: Optional[int]
    #:
    min_value: Optional[float]
    #:
    max_value: Optional[float]
    #:
    start_value: Optional[float]
    #:
    end_value: Optional[str]
    #:
    interval: Optional[float]
    #:
    time_interval: Optional[timedelta]
    #:
    decimals: Optional[int]
    #:
    pattern: Optional[str]
    #:
    start_time: Optional[datetime]
    #:
    end_time: Optional[datetime]


class Facet(BaseModel):
    #:
    type: FacetType = FacetType()
    #:
    value: str = None
    #:
    value_type: Optional[FacetValueType] = None


class Representation(BaseModel):
    #:
    enumerated: ItemScheme = None
    #:
    non_enumerated: List[Facet] = []

    def __repr__(self):
        return '<{}: {}, {}>'.format(self.__class__.__name__,
                                     self.enumerated,
                                     self.non_enumerated)


# 4.4: Concept Scheme

class ISOConceptReference(BaseModel):
    #:
    agency: str
    #:
    id: str
    #:
    scheme_id: str


class Concept(Item):
    #:
    core_representation: Representation = None
    #:
    iso_concept: ISOConceptReference = None


class ConceptScheme(ItemScheme):
    _item_type = Concept
    #:
    items: Dict[str, _item_type] = {}


# 3.3: Basic Inheritance

class Component(IdentifiableArtefact):
    #:
    concept_identity: Concept = None
    #:
    local_representation: Representation = None

    def __contains__(self, value):
        for repr in [self.concept_identity.core_representation,
                     self.local_representation]:
            enum = getattr(repr, 'enumerated', None)
            if enum is not None:
                return value in enum
        raise TypeError('membership not defined for non-enumerated'
                        'representations')


class ComponentList(IdentifiableArtefact):
    #:
    components: List[Component] = []

    auto_order = 1

    # Convenience access to the components
    def append(self, value):
        """Append *value* to :attr:`components`."""
        self.components.append(value)

    def get(self, id, cls=None, **kwargs):
        """Return or create the component with the given *id*.

        Parameters
        ----------
        id : str
            Component ID.
        cls : type, optional
            Hint for the class of a new object.
        kwargs
            Passed to the constructor of :class:`.Component`, or a Component
            subclass if :attr:`.components` is overridden in a subclass of
            ComponentList.
        """
        # TODO use an index to speed up
        # TODO don't return missing items or add an option to avoid this

        # Search for an existing Component
        for c in self.components:
            if c.id == id:
                return c

        # No match

        # Create a new object of a class:
        # 1. Given by the cls argument,
        # 2. Specified by a subclass' _default_type attribute, or
        # 3. Hinted for a subclass' components attribute.
        cls = cls or getattr(self, '_default_type',
                             get_class_hint(self, 'components'))
        component = cls(id=id, **kwargs)

        if 'order' not in kwargs:
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
    def __getitem__(self, key):
        """Convenience access to components."""
        return self.components[key]

    def __len__(self):
        return len(self.components)

    def __iter__(self):
        return iter(self.components)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__,
                                 '; '.join(map(repr, self.components)))

    def __eq__(self, other):
        """ID equal and same components occur in same order."""
        return super().__eq__(other) and \
            all(s == o for s, o in zip(self.components, other.components))


# 4.3: Codelist

class Code(Item):
    """SDMX-IM Code."""


class Codelist(ItemScheme):
    _item_type = Code
    #:
    items: Dict[str, _item_type] = {}


# 4.5: Category Scheme

class Category(Item):
    """SDMX-IM Category."""


class CategoryScheme(ItemScheme):
    _item_type = Category
    #:
    items: Dict[str, _item_type] = {}


class Categorisation(MaintainableArtefact):
    #:
    category: Category = None
    #:
    artefact: IdentifiableArtefact = None


# 4.6: Organisations

class Contact(BaseModel):
    """Organization contact information.

    IMF is the only data provider that returns messages with :class:`Contact`
    information. These differ from the IM in several ways. This class reflects
    these differences:

    - 'name' and 'org_unit' are InternationalString, instead of strings.
    - 'email' may be a list of e-mail addresses, rather than a single address.
    - 'uri' may be a list of URIs, rather than a single URI.
    """
    #:
    name: InternationalString = InternationalString()
    #:
    org_unit: InternationalString = InternationalString()
    #:
    telephone: str = None
    #:
    responsibility: InternationalString = InternationalString()
    #:
    email: List[str]
    #:
    uri: List[str]


class Organisation(Item):
    #:
    contact: List[Contact] = []


Agency = Organisation


class DataProvider(Organisation):
    """SDMX-IM DataProvider."""


# Update forward references to 'Agency'
for cls in list(locals().values()):
    if isclass(cls) and issubclass(cls, MaintainableArtefact):
        cls.update_forward_refs()


# Skip the abstract OrganisationScheme class, since it has no particular
# functionality

class AgencyScheme(ItemScheme):
    _item_type = Agency
    #:
    items: Dict[str, _item_type] = {}


class DataProviderScheme(ItemScheme):
    _item_type = DataProvider
    #:
    items: Dict[str, _item_type] = {}


# 10.2: Constraint inheritance

class ConstrainableArtefact(BaseModel):
    """SDMX-IM ConstrainableArtefact."""


# 10.3: Constraints

class ConstraintRole(BaseModel):
    #:
    role: ConstraintRoleType


class ComponentValue(BaseModel):
    #:
    value_for: Component
    #:
    value: str


class DataKey(BaseModel):
    #: :obj:`True` if the :attr:`keys` are included in the
    #: :class:`.Constraint`; :obj:`False` if they are excluded.
    included: bool
    #: Mapping from :class:`.Component` to :class:`.ComponentValue` comprising
    #: the key.
    key_value: Dict[Component, ComponentValue]


class DataKeySet(BaseModel):
    #: :obj:`True` if the :attr:`keys` are included in the
    #: :class:`.Constraint`; :obj:`False` if they are excluded.
    included: bool
    #: :class:`DataKeys <.DataKey>` appearing in the set.
    keys: List[DataKey]


class Constraint(MaintainableArtefact):
    #: :class:`.DataKeySet` included in the Constraint.
    data_content_keys: Optional[DataKeySet] = None
    # metadata_content_keys: MetadataKeySet = None
    # NB the spec gives 1..* for this attribute, but this implementation allows
    # only 1
    role: ConstraintRole

    # NB this is required to prevent “unhashable type: 'dict'” in pydantic
    class Config:
        validate_assignment = False


class SelectionValue(BaseModel):
    """SDMX-IM SelectionValue."""


class MemberValue(SelectionValue):
    #:
    value: str
    #:
    cascade_values: bool = None

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, KeyValue):
            return self.value == other.value
        else:
            return self.value == other


class MemberSelection(BaseModel):
    #:
    included: bool = True
    #:
    values_for: Component
    #: NB the spec does not say what this feature should be named
    values: Set[MemberValue] = set()

    def __contains__(self, value):
        """Compare KeyValue to MemberValue."""
        return any(mv == value for mv in self.values)


class CubeRegion(BaseModel):
    #:
    included: bool = True
    #:
    member: Dict['Dimension', MemberSelection] = {}

    def __contains__(self, key):
        for ms in self.member.values():
            if key[ms.values_for.id] not in ms:
                return False
        return True

    def to_query_string(self, structure):
        all_values = []

        for dim in structure.dimensions:
            if isinstance(dim, TimeDimension):
                # TimeDimensions handled by query parameters
                continue
            ms = self.member.get(dim, None)
            values = sorted(mv.value for mv in ms.values) if ms else []
            all_values.append('+'.join(values))

        return '.'.join(all_values)


class ContentConstraint(Constraint):
    #: :class:`CubeRegions <.CubeRegion>` included in the ContentConstraint.
    data_content_region: List[CubeRegion] = []
    #:
    content: Set[ConstrainableArtefact] = set()
    # metadata_content_region: MetadataTargetRegion = None

    # NB this is required to prevent RecursionError in pydantic;
    #    see https://github.com/samuelcolvin/pydantic/issues/524
    class Config:
        validate_assignment_exclude = 'data_content_region'

    def __contains__(self, value):
        if self.data_content_region:
            return any(value in cr for cr in self.data_content_region)
        else:
            raise NotImplementedError(
                'ContentConstraint does not contain a CubeRegion.')

    def to_query_string(self, structure):
        cr_count = len(self.data_content_region)
        try:
            if cr_count > 1:
                warn(f'to_query_string() using first of {cr_count} '
                     'CubeRegions.')

            return self.data_content_region[0].to_query_string(structure)
        except IndexError:
            raise RuntimeError(
                'ContentConstraint does not contain a CubeRegion.')


class AttachmentConstraint(Constraint):
    #:
    attachment: Set[ConstrainableArtefact] = set()


# 5.2: Data Structure Defintion

class DimensionComponent(Component):
    #:
    order: Optional[int]


class Dimension(DimensionComponent):
    """SDMX-IM Dimension."""


CubeRegion.update_forward_refs()


class TimeDimension(DimensionComponent):
    """SDMX-IM TimeDimension."""


class MeasureDimension(DimensionComponent):
    """SDMX-IM MeasureDimension."""


class PrimaryMeasure(Component):
    """SDMX-IM PrimaryMeasure."""


class MeasureDescriptor(ComponentList):
    #:
    components: List[PrimaryMeasure] = []


class AttributeRelationship(BaseModel):
    #:
    dimensions: List[Dimension] = []
    #:
    group_key: 'GroupDimensionDescriptor' = None


NoSpecifiedRelationship = AttributeRelationship
PrimaryMeasureRelationship = AttributeRelationship
DimensionRelationship = AttributeRelationship

# 'Retained for compatibility reasons' in SDMX 2.1; not used by pandaSDMX
# GroupRelationship = AttributeRelationship


class DataAttribute(Component):
    #:
    related_to: AttributeRelationship = None
    #:
    usage_status: UsageStatus = None


class ReportingYearStartDay(DataAttribute):
    pass


class AttributeDescriptor(ComponentList):
    #:
    components: List[DataAttribute] = []


class Structure(MaintainableArtefact):
    #:
    grouping: ComponentList = None


class StructureUsage(MaintainableArtefact):
    #:
    structure: Structure = None


class DimensionDescriptor(ComponentList):
    """Describes a set of dimensions.

    IM: “An ordered set of metadata concepts that, combined, classify a
    statistical series, and whose values, when combined (the key) in an
    instance such as a data set, uniquely identify a specific observation.”
    """
    #: :class:`list` (ordered) of :class:`Dimension`,
    #: :class:`MeasureDimension`, and/or :class:`TimeDimension`.
    components: List[DimensionComponent] = []
    _default_type = Dimension

    def assign_order(self):
        """Assign the :attr:`.DimensionComponent.order` attribute.

        The Dimensions in :attr:`components` are numbered, starting from 1.
        """
        for i, component in enumerate(self.components):
            component.order = i + 1

    def order_key(self, key):
        """Return a key ordered according to the DSD."""
        result = key.__class__()
        for dim in sorted(self.components, key=attrgetter('order')):
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
            dd.components.append(Dimension(
                id=id,
                local_representation=Representation(enumerated=cl),
                order=order,
            ))
        return dd


class GroupDimensionDescriptor(DimensionDescriptor):
    #:
    attachment_constraint: bool = None
    #:
    constraint: AttachmentConstraint = None

    def assign_order(self):
        """:meth:`assign_order` has no effect for GroupDimensionDescriptor."""
        pass


AttributeRelationship.update_forward_refs()
# GroupRelationship.update_forward_refs()


@validate_dictlike('group_dimensions')
class DataStructureDefinition(Structure, ConstrainableArtefact):
    """Defines a data structure. Referred to as “DSD”."""
    #: A :class:`AttributeDescriptor` that describes the attributes of the
    #: data structure.
    attributes: AttributeDescriptor = AttributeDescriptor()
    #: A :class:`DimensionDescriptor` that describes the dimensions of the
    #: data structure.
    dimensions: DimensionDescriptor = DimensionDescriptor()
    #: A :class:`.MeasureDescriptor`.
    measures: MeasureDescriptor = None
    #: A :class:`.GroupDimensionDescriptor`.
    group_dimensions: DictLike[str, GroupDimensionDescriptor] = DictLike()

    # Convenience methods
    def attribute(self, id, **kwargs):
        """Call :meth:`ComponentList.get` on :attr:`attributes`."""
        return self.attributes.get(id, **kwargs)

    def dimension(self, id, **kwargs):
        """Call :meth:`ComponentList.get` on :attr:`dimensions`."""
        return self.dimensions.get(id, **kwargs)

    def make_constraint(self, key):
        """Return a constraint for *key*.

        *key* is a :class:`dict` wherein:

        - keys are :class:`str` ids of Dimensions appearing in this
          DSD's :attr:`dimensions`, and
        - values are '+'-delimited :class:`str` containing allowable values,
          _or_ iterables of :class:`str`, each an allowable value.

        For example::

            cc2 = dsd.make_constraint({'foo': 'bar+baz', 'qux': 'q1+q2+q3'})

        ``cc2`` includes any key where the 'foo' dimension is 'bar' *or* 'baz',
        *and* the 'qux' dimension is one of 'q1', 'q2', or 'q3'.

        Returns
        -------
        ContentConstraint
            A constraint with one :class:`CubeRegion` in its
            :attr:`data_content_region <ContentConstraint.data_content_region>`
            , including only the values appearing in *keys*.

        Raises
        ------
        ValueError
            if *key* contains a dimension IDs not appearing in
            :attr:`dimensions`.
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

            values = values.split('+') if isinstance(values, str) else values
            for value in values:
                # TODO validate values
                mvs.add(MemberValue(value=value))

            cr.member[dim] = MemberSelection(included=True,
                                             values_for=dim,
                                             values=mvs)

        if len(key):
            raise ValueError('Dimensions {!r} not in {!r}'
                             .format(list(key.keys()), self.dimensions))

        return ContentConstraint(
            data_content_region=[cr],
            role=ConstraintRole(role=ConstraintRoleType.allowable))

    @classmethod
    def from_keys(cls, keys):
        """Return a new DSD given some *keys*.

        The DSD's :attr:`dimensions` refers to a set of new :class:`Concepts
        <Concept>` and :class:`Codelists <Codelist>`, created to represent all
        the values observed across *keys* for each dimension.

        Parameters
        ----------
        keys : iterable of :class:`Key`
            or of subclasses such as :class:`SeriesKey` or :class:`GroupKey`.
        """
        iter_keys = iter(keys)
        dd = DimensionDescriptor.from_key(next(iter_keys))
        for k in iter_keys:
            for i, (id, kv) in enumerate(k.values.items()):
                dd[i].local_representation.enumerated.append(
                    Code(id=kv.value))
        return cls(dimensions=dd)


class DataflowDefinition(StructureUsage, ConstrainableArtefact):
    #:
    structure: DataStructureDefinition = DataStructureDefinition()


# 5.4: Data Set

def value_for_dsd_ref(kind, args, kwargs):
    """Maybe replace a string 'value_for' in *kwargs* with a DSD reference."""
    try:
        dsd = kwargs.pop('dsd')
        descriptor = getattr(dsd, kind + 's')
        kwargs['value_for'] = descriptor.get(kwargs['value_for'])
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
    value_for: Dimension = None

    def __init__(self, *args, **kwargs):
        args, kwargs = value_for_dsd_ref('dimension', args, kwargs)
        super(KeyValue, self).__init__(*args, **kwargs)

    def __eq__(self, other):
        """Compare the value to a Python built-in type, e.g. str."""
        if isinstance(other, (KeyValue, MemberValue)):
            return self.value == other.value
        else:
            return self.value == other

    def __str__(self):
        return '{0.id}={0.value}'.format(self)

    def __repr__(self):
        return '<{0.__class__.__name__}: {0.id}={0.value}>'.format(self)

    def __hash__(self):
        # KeyValue instances with the same id & value hash identically
        return hash(self.id + str(self.value))


TimeKeyValue = KeyValue


class AttributeValue(BaseModel):
    """SDMX-IM AttributeValue.

    In the spec, AttributeValue is an abstract class. Here, it serves as both
    the concrete subclasses CodedAttributeValue and UncodedAttributeValue.
    """
    # TODO separate and enforce properties of Coded- and UncodedAttributeValue
    #:
    value: Union[str, Code]
    #:
    value_for: DataAttribute = None
    #:
    start_date: Optional[date]

    def __init__(self, *args, **kwargs):
        args, kwargs = value_for_dsd_ref('attribute', args, kwargs)
        super(AttributeValue, self).__init__(*args, **kwargs)

    def __eq__(self, other):
        """Compare the value to a Python built-in type, e.g. str."""
        return self.value == other

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<{}: {}={}>'.format(self.__class__.__name__, self.value_for,
                                    self.value)


@validate_dictlike('attrib', 'values')
class Key(BaseModel):
    """SDMX Key class.

    The constructor takes an optional list of keyword arguments; the keywords
    are used as Dimension or Attribute IDs, and the values as KeyValues.

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
        :attr:`~.DataStructureDefinition.attributes` are used to separate the
        *kwargs* into :class:`KeyValues <.KeyValue>` and
        :class:`AttributeValues <.AttributeValue>`. The *kwarg* for
        :attr:`described_by`, if any, must be
        :attr:`~.DataStructureDefinition.dimensions` or appear in
        :attr:`~.DataStructureDefinition.group_dimensions`.
    kwargs
        Dimension and Attribute IDs, and/or the class properties.

    """
    #:
    attrib: DictLike[str, AttributeValue] = DictLike()
    #:
    described_by: DimensionDescriptor = None
    #: Individual KeyValues that describe the key.
    values: DictLike[str, KeyValue] = DictLike()

    def __init__(self, arg=None, **kwargs):
        super().__init__()
        if arg:
            if len(kwargs):
                raise ValueError("Key() accepts either a single argument, or "
                                 "keyword arguments; not both.")
            kwargs.update(arg)

        # DSD argument
        dsd = kwargs.pop('dsd', None)

        # DimensionDescriptor
        dd = kwargs.pop('described_by', None)

        if dsd:
            if not dd:
                dd = dsd.dimensions

            # DD must appear in the DSD if both are supplied
            if (dd is not dsd.dimensions and
                    dd not in dsd.group_dimensions.values()):
                raise ValueError(f'described_by={dd} is not a [Group]'
                                 f'DimensionDescriptor of dsd={dsd}')

            try:
                self.described_by = dd
            except Exception:
                dd = None

        # Convert keyword arguments to either KeyValue or AttributeValue
        values = []
        for order, (id, value) in enumerate(kwargs.items()):
            args = dict(id=id, value=value)

            if dsd and id in dsd.attributes:
                # Reference a DataAttribute from the AttributeDescriptor
                da = dsd.attributes.get(id)
                # Store the attribute value
                self.attrib[da.id] = AttributeValue(**args, value_for=da)
                continue

            if dd:
                # Reference a Dimension from the DimensionDescriptor
                args['value_for'] = dd.get(id)
                # Retrieve the order
                order = args['value_for'].order

            # Store a KeyValue, to be sorted later
            values.append((order, KeyValue(**args)))

        # Sort the values according to *order*
        self.values.update({kv.id: kv for _, kv in sorted(values)})

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
            raise e

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
        if hasattr(other, 'values'):
            return all([a == b for a, b in zip(self.values, other.values)])
        elif isinstance(other, str) and len(self.values) == 1:
            return self.values[0] == other
        else:
            raise ValueError(other)

    def __hash__(self):
        # Hash of the individual KeyValues, in order
        return hash(tuple(hash(kv) for kv in self.values.values()))

    # Representations

    def __str__(self):
        return '({})'.format(', '.join(map(str, self.values.values())))

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__,
                                 ', '.join(map(str, self.values.values())))

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
    id: str = None
    #:
    described_by: GroupDimensionDescriptor = None


class SeriesKey(Key):
    #: :mod:`pandaSDMX` extension not in the IM.
    group_keys: Set[GroupKey] = set()

    @property
    def group_attrib(self):
        """Return a view of combined group attributes."""
        # Needed to pass existing tests
        view = DictLike()
        for gk in self.group_keys:
            view.update(gk.attrib)
        return view


@validate_dictlike('attached_attribute')
class Observation(BaseModel):
    """SDMX-IM Observation.

    This class also implements the spec classes ObservationValue,
    UncodedObservationValue, and CodedObservation.
    """
    #:
    attached_attribute: DictLike[str, AttributeValue] = DictLike()
    #:
    series_key: SeriesKey = None
    #: Key for dimension(s) varying at the observation level.
    dimension: Key = None
    #: Data value.
    value: Union[Any, Code] = None
    #:
    value_for: PrimaryMeasure = None
    #: :mod:`pandaSDMX` extension not in the IM.
    group_keys: Set[GroupKey] = set()

    @property
    def attrib(self):
        """Return a view of combined observation, series & group attributes."""
        view = self.attached_attribute.copy()
        view.update(getattr(self.series_key, 'attrib', {}))
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
        return '{0.key}: {0.value}'.format(self)


@validate_dictlike('attrib')
class DataSet(AnnotableArtefact):
    # SDMX-IM features
    #:
    action: ActionType = None
    #:
    attrib: DictLike[str, AttributeValue] = DictLike()
    #:
    valid_from: str = None
    #:
    structured_by: DataStructureDefinition = None

    #: All observations in the DataSet.
    obs: List[Observation] = []

    #: Map of series key → list of observations.
    #: :mod:`pandaSDMX` extension not in the IM.
    series: DictLike[SeriesKey, List[Observation]] = DictLike()
    #: Map of group key → list of observations.
    #: :mod:`pandaSDMX` extension not in the IM.
    group: DictLike[GroupKey, List[Observation]] = DictLike()

    def _add_group_refs(self, target):
        """Associate *target* with groups in this dataset.

        *target* may be an instance of SeriesKey or Observation.
        """
        for group_key in self.group:
            if group_key in (target if isinstance(target, SeriesKey) else
                             target.key):
                target.group_keys.add(group_key)
                if isinstance(target, Observation):
                    self.group[group_key].append(target)

    def add_obs(self, observations, series_key=None):
        """Add *observations* to a series with *series_key*.

        Checks consistency and adds group associations."""
        if series_key:
            # Associate series_key with any GroupKeys that apply to it
            self._add_group_refs(series_key)
            if series_key not in self.series:
                # Initialize empty series
                self.series[series_key] = []

        for obs in observations:
            # Associate the observation with any GroupKeys that contain it
            self._add_group_refs(obs)

            # Store a reference to the observation
            self.obs.append(obs)

            if series_key:
                # Check that the Observation is not associated with a different
                # SeriesKey
                assert obs.series_key is series_key, \
                    (obs.series_key, id(obs.series_key), series_key,
                     id(series_key))
                # Store a reference to the observation
                self.series[series_key].append(obs)

    @validator('action')
    def _validate_action(cls, value):
        if value in ActionType:
            return value
        else:
            return ActionType[value]


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


# 11. Data Provisioning

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
    structure_usage: StructureUsage = None
    #:
    data_provider: DataProvider = None
