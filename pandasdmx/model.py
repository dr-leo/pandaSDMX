"""SDMX Information Model (SDMX-IM)

This module implements many of the classes described in the SDMX-IM
specification ('spec'), which is available from:

- https://sdmx.org/?page_id=5008
- https://sdmx.org/wp-content/uploads/
    SDMX_2-1-1_SECTION_2_InformationModel_201108.pdf

Details of the implementation:

- the IPython traitlets package is used to enforce the types of attributes
  that reference instances of other classes. Two custom trait types are used:

  - DictLikeTrait: a dict-like object that adds both attribute access by name,
    and integer index access. See pandasdmx.util.
  - InternationalStringTrait.

- some classes have additional attributes not mentioned in the spec, to ease
  navigation between related objects. These are marked with comments "pandaSDMX
  extensions not in the IM".
- class definitions are grouped by section of the spec, but these sections
  appear out of order so that dependent classes are defined first.

"""
# TODO for a complete implementation of the spec
# - Enforce TimeKeyValue (instead of KeyValue) for {Generic,StructureSpecific}
#   TimeSeriesDataSet.
#
# TODO for convenience
# - Guess URNs using the standard format.

from copy import copy
from datetime import date, datetime, timedelta
from enum import Enum
from operator import attrgetter

from traitlets import (
    Any,
    Bool,
    CFloat,
    CInt,
    Dict,
    Float,
    HasTraits,
    Instance,
    Int,
    List,
    Set,
    This,
    TraitType,
    Unicode,
    Union,
    UseEnum,
    )

from pandasdmx.util import DictLike, DictLikeTrait


# TODO read this from the environment, or use any value set in the SDMX XML
# spec. Currently set to 'en' because test_dsd.py expects it
DEFAULT_LOCALE = 'en'


# 3.2: Base structures

class InternationalString(HasTraits):
    """SDMX-IM InternationalString.

    SDMX-IM LocalisedString is not implemented. Instead, the 'localizations' is
    a mapping where:

     - keys correspond to the 'locale' property of LocalisedString.
     - values correspond to the 'label' property of LocalisedString.
    """
    localizations = Dict(Instance(Unicode))

    def __init__(self, value=None, **kwargs):
        if isinstance(value, str):
            self.localizations[DEFAULT_LOCALE] = value
        elif isinstance(value, tuple) and len(value) == 2:
            self.localizations[value[0]] = value[1]
        elif value is None:
            self.localizations.update(kwargs)
        else:
            raise ValueError

    # Convenience access
    def __getitem__(self, locale):
        return self.localizations[locale]

    def __setitem__(self, locale, label):
        self.localizations[locale] = label

    # Duplicate of __getitem__, to pass existing tests in test_dsd.py
    def __getattr__(self, locale):
        try:
            return self._trait_values['localizations'][locale]
        except KeyError:
            super(HasTraits, self).__getattr__(locale)

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


class InternationalStringTrait(TraitType):
    """Trait type for InternationalString.

    With trailets.Instance, a locale must be provided for every label:

    >>> class Foo(HasTraits):
    >>>     name = Instance(InternationalString)
    >>>
    >>> f = Foo()
    >>> f.name['en'] = "Foo's name in English"

    With InternationalStringTrait, the DEFAULT_LOCALE is automatically selected
    when setting with a string:

    >>> class Bar(HasTraits):
    >>>     name = InternationalStringTrait
    >>>
    >>> b = Bar()
    >>> b.name = "Bar's name in English"

    """
    def make_dynamic_default(self):
        return InternationalString()

    def validate(self, obj, value):
        if isinstance(value, InternationalString):
            return value
        try:
            return obj._trait_values.get(self.name, InternationalString()) + \
                InternationalString(value)
        except ValueError:
            self.error(obj, value)


class Annotation(HasTraits):
    id = Unicode()
    title = Unicode()
    type = Unicode()
    url = Unicode()

    text = InternationalStringTrait()


class AnnotableArtefact(HasTraits):
    annotations = List(Instance(Annotation))


class IdentifiableArtefact(AnnotableArtefact):
    """SDMX-IM IdentifiableArtefact."""
    id = Unicode()
    uri = Unicode()
    urn = Unicode()

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
        return self.id

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.id)


class NameableArtefact(IdentifiableArtefact):
    name = InternationalStringTrait()
    description = InternationalStringTrait(allow_none=True)

    def __repr__(self):
        return "<{}: '{}'='{}'>".format(
            self.__class__.__name__,
            self.id,
            str(self.name))


class VersionableArtefact(NameableArtefact):
    version = Unicode()
    valid_from = Unicode(allow_none=True)
    valid_to = Unicode(allow_none=True)


class MaintainableArtefact(VersionableArtefact):
    is_final = Bool()
    is_external_reference = Bool()
    service_url = Unicode()
    structure_url = Unicode()
    maintainer = Instance('pandasdmx.model.Agency')


# 3.4: Data Types

ActionType = Enum('ActionType', 'delete replace append information')

UsageStatus = Enum('UsageStatus', 'mandatory conditional')

FacetValueType = Enum(
    'FacetValueType',
    'string bigInteger integer long short decimal float double boolean uri '
    'count inclusiveValueRange alpha alphaNumeric numeric exclusiveValueRange '
    'incremental observationalTimePeriod standardTimePeriod basicTimePeriod '
    'gregorianTimePeriod gregorianYearMonth gregorianDay reportingTimePeriod '
    'reportingYear reportingSemester reportingTrimester reportingQuarter '
    'reportingMonth reportingWeek reportingDay dateTime timesRange month '
    'monthDay day time duration keyValues identifiableReference '
    'dataSetReference')


# 3.5: Item Scheme

class Item(NameableArtefact):
    parent = Instance('pandasdmx.model.Item', allow_none=True)
    child = List(Instance(This))

    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)

        # Add this Item as a child of its parent
        parent = kwargs.get('parent', None)
        if parent and self not in parent:
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


class ItemScheme(MaintainableArtefact):
    is_partial = Bool()
    items = List(Instance(Item))

    # Convenience access to items
    def __getattr__(self, name):
        # Provided to pass test_dsd.py
        for i in self._trait_values.get('items', []):
            if i.id == name:
                return i
        raise AttributeError(name)

    def __getitem__(self, name):
        for i in self.items:
            if i.id == name:
                return i
        raise KeyError(name)

    def __contains__(self, item):
        """Recursive containment."""
        for i in self.items:
            if item == i or item in i:
                return True

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
        if obj:
            assert not len(kwargs), ValueError('cannot give both *obj* and '
                                               'keyword arguments to '
                                               'setdefault()')
        else:
            # Replace a string 'parent' ID with a reference to the object
            parent = kwargs.pop('parent', None)
            if isinstance(parent, str):
                kwargs['parent'] = self[parent]

            # Instantiate an object of the correct class by introspecting
            # the items trait
            obj = self.__class__.items._trait.klass(**kwargs)

        if obj not in self.items:
            # Add the object to the ItemScheme
            self.items.append(obj)

        return obj


# 3.6: Structure

class FacetType(HasTraits):
    isSequence = Bool()
    min_length = CInt()
    max_length = CInt()
    min_value = CFloat()
    max_value = CFloat()
    start_value = Float()
    end_value = Unicode()
    interval = Float()
    time_interval = Instance(timedelta)
    decimals = Int()
    pattern = Unicode()
    start_time = Instance(datetime)
    end_time = Instance(datetime)


class Facet(HasTraits):
    type = Instance(FacetType, args=())
    value = Unicode()
    value_type = UseEnum(FacetValueType)


class Representation(HasTraits):
    enumerated = Instance(ItemScheme)
    non_enumerated = Set(Instance(Facet))


# 4.4: Concept Scheme

class ISOConceptReference(HasTraits):
    agency = Unicode()
    id = Unicode()
    scheme_id = Unicode()


class Concept(Item):
    core_representation = Instance(Representation, allow_none=True)
    iso_concept = Instance(ISOConceptReference)


class ConceptScheme(ItemScheme):
    items = List(Instance(Concept))


# 3.3: Basic Inheritance

class Component(IdentifiableArtefact):
    concept_identity = Instance(Concept)
    local_representation = Instance(Representation, args=(), allow_none=True)


class ComponentList(IdentifiableArtefact):
    components = List(Instance(Component))

    # Convenience access to the components
    def append(self, value):
        self.components.append(value)

    def get(self, id, **kwargs):
        """Return or create the component with the given *id*.

        The *kwargs* are passed to the constructor of Component(), or a
        subclass if 'components' is overridden in a subclass of ComponentList.
        """
        # TODO use an index to speed up

        # Chose an appropriate class specified for the trait in the
        # ComponentList subclass.
        trait = self.__class__.components._trait
        try:
            klass = trait.klass
        except AttributeError:
            # Union trait
            klass = trait.trait_types[0].klass

        # Create the candidate
        candidate = klass(id=id, **kwargs)

        # Search for a match
        for c in self.components:
            if c == candidate:
                # Same Component, difference instance. Discard the candidate
                return c

        # No match; store and return the candidate
        self.components.append(candidate)
        return candidate

    # Properties of components
    def __len__(self):
        return len(self.components)

    def __iter__(self):
        return iter(self.components)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__,
                                 '; '.join(map(repr, self.components)))


# 4.3: Codelist

class Code(Item):
    pass


class Codelist(ItemScheme):
    items = List(Instance(Code))


# 4.5: Category Scheme

class Category(Item):
    pass


class CategoryScheme(ItemScheme):
    items = List(Instance(Category))


class Categorisation(MaintainableArtefact):
    category = Instance(Category)
    artefact = Instance(IdentifiableArtefact)


# 4.6: Organisations

class Contact(HasTraits):
    """Organization contact information.

    IMF is the only data provider that returns messages with :class:`Contact`
    information. These differ from the IM in several ways. This class reflects
    these differences:

    - 'name' and 'org_unit' are InternationalString, instead of strings.
    - 'email' may be a list of e-mail addresses, rather than a single address.
    - 'uri' may be a list of URIs, rather than a single URI.
    """
    name = InternationalStringTrait()
    org_unit = InternationalStringTrait()
    telephone = Unicode(allow_none=True)
    responsibility = InternationalStringTrait()
    email = List(Unicode())
    uri = List(Unicode())


class Organisation(Item):
    contact = List(Instance(Contact))
    pass


Agency = Organisation
DataProvider = Organisation


# Skip the abstract OrganisationScheme class, since it has no particular
# functionality

class AgencyScheme(ItemScheme):
    items = List(Instance(Agency))


class DataProviderScheme(ItemScheme):
    items = List(Instance(DataProvider))


# 10.2: Constraint inheritance

class ConstrainableArtefact:
    pass


# 10.3: Constraints

ConstraintRoleType = Enum('ConstraintRoleType', 'allowable actual')


class ConstraintRole(HasTraits):
    role = UseEnum(ConstraintRoleType)


# class ComponentValue(HasTraits):
#     value_for = Instance(Component)
#     value = Unicode()
#
#
# class DataKey(HasTraits):
#     is_included = Bool()
#     key_value = List(Instance(ComponentValue))
#
#
# class DataKeySet(HasTraits):
#     is_included = Bool()
#     keys = List(Instance(DataKey))


class Constraint(MaintainableArtefact):
    # data_content_keys = Instance(DataKeySet, allow_none=True)
    # metadata_content_keys = Instance(MetadataKeySet, allow_none=True)
    role = Set(Instance(ConstraintRole))


class SelectionValue(HasTraits):
    pass


class MemberValue(SelectionValue):
    value = Unicode()
    cascade_values = Bool()


class MemberSelection(HasTraits):
    included = Bool()
    values_for = Instance(Component)
    values = Set(Instance(MemberValue))


class CubeRegion(HasTraits):
    included = Bool()
    member = Dict(Instance(MemberSelection))

    def __contains__(self, v):
        key, value = v
        kv = self.key_values
        if key not in kv.keys():
            raise KeyError(
                'Unknown key: {0}. Allowed keys are: {1}'.format(
                    key, list(kv.keys())))
        return (value in kv[key]) == self.include

    def to_query_string(self, structure):
        all_values = []
        for dim in structure.dimensions:
            ms = self.member.get(dim, None)
            values = sorted(mv.value for mv in ms.values) if ms else []
            all_values.append('+'.join(values))

        return '.'.join(all_values)


class ContentConstraint(Constraint):
    data_content_region = Instance(CubeRegion, allow_none=True)
    # metadata_content_region = Instance(MetadataTargetRegion, allow_none=True)

    def __contains__(self, v):
        if self.data_content_region:
            result = [v in c for c in self.data_content_region]
            # Remove all cubes where v passed. The remaining ones indicate
            # fails.
            if True in result:
                result.remove(True)
            if result == []:
                return True
            else:
                raise ValueError('Key outside cube region(s).', v, result)
        else:
            raise NotImplementedError(
                'ContentConstraint does not contain a CubeRegion.')

    def to_query_string(self, structure):
        try:
            return self.data_content_region.to_query_string(structure)
        except AttributeError as e:
            raise NotImplementedError(
                'ContentConstraint does not contain a CubeRegion.')


# 5.2: Data Structure Defintion

class DimensionComponent(Component):
    order = Int()


class Dimension(DimensionComponent):
    pass


class TimeDimension(DimensionComponent):
    pass


class MeasureDimension(DimensionComponent):
    pass


class PrimaryMeasure(Component):
    pass


class MeasureDescriptor(ComponentList):
    components = List(Instance(PrimaryMeasure))


class AttributeRelationship(HasTraits):
    dimensions = List(Instance(Dimension))
    group = Instance('pandasdmx.model.GroupDimensionDescriptor',
                     allow_none=True)


NoSpecifiedRelationship = AttributeRelationship
PrimaryMeasureRelationship = AttributeRelationship
GroupRelationship = AttributeRelationship
DimensionRelationship = AttributeRelationship


class DataAttribute(Component):
    related_to = Instance(AttributeRelationship)
    usage_status = Instance(UsageStatus)


class ReportingYearStartDay(DataAttribute):
    pass


class AttributeDescriptor(ComponentList):
    components = List(Instance(DataAttribute))


class Structure(MaintainableArtefact):
    grouping = Instance(ComponentList)


class StructureUsage(MaintainableArtefact):
    structure = Instance(Structure)


class DimensionDescriptor(ComponentList):
    components = List(Union([
        Instance(Dimension),
        Instance(MeasureDimension),
        Instance(TimeDimension),
        ]))

    def __getitem__(self, key):
        """Convenience access to components."""
        return self.components[key]

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

        For each KeyValue in the *key*:
        - A new Dimension is created.
        - A new Codelist is created, containing the KeyValue.value.
        """
        dd = cls()
        for id, kv in key.values.items():
            d = Dimension(id=id)
            cl = Codelist(id=id)
            d.local_representation.enumerated = cl
            cl.items.append(Code(id=kv.value))
            dd.components.append(d)
        return dd


class GroupDimensionDescriptor(DimensionDescriptor):
    attachment_constraint = Bool()
    # constraint = Instance(AttachmentConstraint, allow_none=True)


class DataStructureDefinition(Structure, ConstrainableArtefact):
    attributes = Instance(AttributeDescriptor, args=())
    dimensions = Instance(DimensionDescriptor, args=())
    measures = Instance(MeasureDescriptor)
    group_dimensions = Instance(GroupDimensionDescriptor)

    # Convenience methods
    def attribute(self, id, **kwargs):
        return self.attributes.get(id, **kwargs)

    def dimension(self, id, **kwargs):
        return self.dimensions.get(id, **kwargs)

    def make_cube(self, keys):
        """Return a ContentConstraint for a dict of *keys*."""
        # TODO validate values
        cr = CubeRegion()
        for dim in self.dimensions:
            try:
                values = keys.pop(dim.id)
            except KeyError:
                continue
            ms = MemberSelection(included=True, values_for=dim)
            for value in values.split('+'):
                ms.values.add(MemberValue(value=value))
            cr.member[dim] = ms
        assert len(keys) == 0
        return ContentConstraint(data_content_region=cr)

    @classmethod
    def from_keys(cls, keys):
        """Create a new DataStructureDefinition from some *keys*.

        The DSD.dimensions refers to a set of Concepts and Codelists, each
        containing all the values observed across *keys* for that dimension.
        """
        iter_keys = iter(keys)
        dd = DimensionDescriptor.from_key(next(iter_keys))
        for k in iter_keys:
            for i, (id, kv) in enumerate(k.values.items()):
                dd[i].local_representation.enumerated.items.append(
                    Code(id=kv.value))
        return cls(dimensions=dd)


class DataflowDefinition(StructureUsage, ConstrainableArtefact):
    structure = Instance(DataStructureDefinition, args=())


# 5.4: Data Set

class KeyValue(HasTraits):
    id = Unicode()
    value = Any()

    def __eq__(self, other):
        """Compare the value to a Python built-in type, e.g. str."""
        return self.value == other

    def __str__(self):
        return '{0.id}={0.value}'.format(self)

    def __repr__(self):
        return '<{0.__class__.__name__}: {0.id}={0.value}>'.format(self)

    def __hash__(self):
        # KeyValue instances with the same id & value hash identically
        return hash(self.id + str(self.value))


TimeKeyValue = KeyValue


def value_for_dsd_ref(args, kwargs):
    """Maybe replace a string 'value_for' in *kwargs* with a DSD reference."""
    try:
        dsd = kwargs.pop('dsd')
        kwargs['value_for'] = dsd.attributes.get(kwargs['value_for'])
    except KeyError:
        pass
    return args, kwargs


class AttributeValue(HasTraits):
    """SDMX-IM AttributeValue.

    In the spec, AttributeValue is an abstract class. Here, it serves as both
    the concrete subclasses CodedAttributeValue and UncodedAttributeValue.
    """
    # TODO separate and enforce properties of Coded- and UncodedAttributeValue
    value = Union([Unicode(), Instance(Code)])
    value_for = Instance(DataAttribute, allow_none=True)
    start_date = Instance(date)

    def __init__(self, *args, **kwargs):
        args, kwargs = value_for_dsd_ref(args, kwargs)
        super(AttributeValue, self).__init__(*args, **kwargs)

    def __eq__(self, other):
        """Compare the value to a Python built-in type, e.g. str."""
        return self.value == other

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<{}: {}={}>'.format(self.__class__.__name__, self.value_for,
                                    self.value)


class Key(HasTraits):
    """SDMX Key class.

    The constructor takes an optional list of keyword arguments; the keywords
    are used as Dimension IDs, and the values as KeyValues.

    For convience, the values of the key may be accessed directly:

    >>> k = Key(foo=1, bar=2)
    >>> k.values['foo']
    1
    >>> k['foo']
    1

    """
    attrib = DictLikeTrait(Instance(AttributeValue))
    values = DictLikeTrait(Instance(KeyValue))
    described_by = Instance(DimensionDescriptor, allow_none=True)

    def __init__(self, arg=None, **kwargs):
        if arg:
            if len(kwargs):
                raise ValueError("Key() accepts either a single argument, or "
                                 "keyword arguments; not both.")
            kwargs.update(arg)
        self.described_by = kwargs.pop('described_by', None)
        for id, value in kwargs.items():
            self.values[id] = KeyValue(id=id, value=value)

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
            # To avoid recursion, use the underlying traitlets private member
            return self._trait_values['values'][name]
        except KeyError:
            raise AttributeError

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
    id = Unicode()
    described_by = Instance(GroupDimensionDescriptor, allow_none=True)


class SeriesKey(Key):
    # pandaSDMX extensions not in the IM
    group_keys = Set(Instance(GroupKey))

    @property
    def group_attrib(self):
        """Return a view of combined group attributes."""
        # Needed to pass existing tests
        view = DictLike()
        for gk in self.group_keys:
            view.update(gk.attrib)
        return view


class Observation(HasTraits):
    """SDMX-IM Observation.

    This class also implements the spec classes ObservationValue,
    UncodedObservationValue, and CodedObservation.
    """
    attached_attribute = DictLikeTrait(Instance(AttributeValue))
    series_key = Instance(SeriesKey, allow_none=True)
    dimension = Instance(Key, allow_none=True)
    value = Union([Any(), Instance(Code)])
    value_for = Instance(PrimaryMeasure, allow_none=True)

    # pandaSDMX extensions not in the IM
    group_keys = Set(Instance(GroupKey))

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


class DataSet(AnnotableArtefact):
    # SDMX-IM features
    action = UseEnum(ActionType)
    attrib = DictLikeTrait(Instance(AttributeValue))
    valid_from = Unicode(allow_none=True)
    structured_by = Instance(DataStructureDefinition)
    obs = List(Instance(Observation))

    # pandaSDMX extensions not in the IM
    # Map of series key → list of observations
    series = DictLikeTrait(List(Instance(Observation)))
    # Map of group key → list of observations
    group = DictLikeTrait(List(Instance(Observation)))

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
                assert obs.series_key is series_key
                # Store a reference to the observation
                self.series[series_key].append(obs)


class _AllDimensions:
    pass


AllDimensions = _AllDimensions()
