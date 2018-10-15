"""SDMX Information Model (SDMX-IM)

This module implements many of the classes described in the SDMX-IM
specification ('spec'), which is available from:

- https://sdmx.org/?page_id=5008
- https://sdmx.org/wp-content/uploads/
    SDMX_2-1-1_SECTION_2_InformationModel_201108.pdf

Details of the implementation:
- the IPython traitlets package is used to enforce the types of attributes
  that reference instances of other classes. Two custom trait types are used:
  - DictLikeTrait: a dict-like object with attribute and integer index access.
    See pandasdmx.util.
  - InternationalStringTrait.
- class definitions are grouped by section of the spec, but these section
  appear out of order so that dependent classes are defined first.

The module also implements extra classes that are NOT described in the spec,
but are used in XML and JSON messages: Message, StructureMessage, DataMessage,
Header, and Footer. These appear last

"""
from copy import copy
from datetime import date, datetime, timedelta
from enum import Enum
from operator import attrgetter

from traitlets import (
    Any,
    Bool,
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

from pandasdmx.util import DictLikeTrait


# TODO read this from the environment
DEFAULT_LOCALE = 'EN_ca'


# 3.2: Base structures

class InternationalString(HasTraits):
    """SDMX-IM InternationalString.

    SDMX-IM LocalisedString is not implemented. Instead, the 'localizations' is
    a mapping where:
     - keys correspond to the 'locale' property of LocalisedString.
     - values correspond to the 'label' property of LocalisedString.
    """
    localizations = Dict(Instance(Unicode))

    def __init__(self, value=None):
        if isinstance(value, str):
            self.localizations[DEFAULT_LOCALE] = value
        elif isinstance(value, tuple) and len(value) == 2:
            self.localizations[value[0]] = value[1]
        elif value is None:
            pass
        else:
            raise ValueError

    def set_label(self, value):
        self.localizations[DEFAULT_LOCALE] = value

    # Convenience access
    def __getitem__(self, locale):
        return self.localizations[locale]

    def __setitem__(self, locale, label):
        self.localizations[locale] = label

    def __add__(self, other):
        result = copy(self)
        result.localizations.update(other.localizations)
        return result

    def __str__(self):
        return self.localizations[DEFAULT_LOCALE]

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
    default_value = InternationalString()

    def validate(self, obj, value):
        if isinstance(value, InternationalString):
            return value
        try:
            return obj._trait_values[self.name] + InternationalString(value)
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
    id = Unicode()
    uri = Unicode()
    urn = Unicode()

    # TODO is this the right comparison? What about objects where URN is not
    # provided?
    def __eq__(self, value):
        return self.urn == value.urn

    def __ne__(self, value):
        return self.urn != value.urn

    def __lt__(self, value):
        return self.urn < value.urn

    def __gt__(self, value):
        return self.urn > value.urn

    def __le__(self, value):
        return self.urn <= value.urn

    def __ge__(self, value):
        return self.urn >= value.urn

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.id

    def __repr__(self):
        result = ' | '.join(
            (self.__class__.__name__, self.id))
        return result


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
    final = Bool()
    is_external_reference = Bool()
    service_url = Unicode()
    structure_url = Unicode()
    maintainer = Instance('pandasdmx.model.Agency')


# 3.4: Data Types

ActionType = Enum('ActionType', 'delete replace append information')

UsageStatus = Enum('UsageStatus', 'mandatory conditional')

FacetValueType = Enum(
    'FacetValueType',
    'string bigInteger integer long short decimal float double boolean uri'
    'count inclusiveValueRange alpha alphaNumeric numeric exclusiveValueRange'
    'incremental observationalTimePeriod standardTimePeriod basicTimePeriod'
    'gregorianTimePeriod gregorianYearMonth gregorianDay reportingTimePeriod'
    'reportingYear reportingSemester reportingTrimester reportingQuarter'
    'reportingMonth reportingWeek reportingDay dateTime timesRange month'
    'monthDay day time duration keyValues identifiableReference'
    'dataSetReference')


# 3.5: Item Scheme

class Item(NameableArtefact):
    parent = Instance(This, allow_none=True)
    child = List(Instance(This))


class ItemScheme(MaintainableArtefact):
    is_partial = Bool()
    items = List(Instance(Item))

    def __repr__(self):
        return "<{}: '{}', {} items>".format(
            self.__class__.__name__,
            self.id,
            len(self.items))


# 3.6: Structure

class FacetType(HasTraits):
    isSequence = Bool()
    min_length = Int()
    max_length = Int()
    min_value = Float()
    max_value = Float()
    start_value = Float()
    end_value = Unicode()
    interval = Float()
    time_interval = Instance(timedelta)
    decimals = Int()
    pattern = Unicode()
    start_time = Instance(datetime)
    end_time = Instance(datetime)


class Facet(HasTraits):
    type = Instance(FacetType)
    value = Unicode()
    value_type = UseEnum(FacetValueType)


class Representation:
    enumerated = List(Instance(ItemScheme))
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
    local_representation = Instance(Representation)


class ComponentList(IdentifiableArtefact):
    components = List(Instance(Component))

    # Convenience access to the components
    def append(self, value):
        self.components.append(value)

    def __iter__(self):
        return iter(self.components)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__,
                                 '; '.join(map(str, self.components)))


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

class Organisation(Item):
    pass


class Agency(Organisation):
    pass


# 10.2: Constraint inheritance

class ConstrainableArtefact:
    pass


# 10.3: Constraints

ConstraintRoleType = Enum('ConstraintRoleType', 'allowable actual')


class ConstraintRole(HasTraits):
    role = UseEnum(ConstraintRoleType)


class Constraint(MaintainableArtefact):
    # data_content_keys = Instance(DataKeySet, allow_none=True)
    # metadata_content_keys = Instance(MetadataKeySet, allow_none=True)
    role = Set(Instance(ConstraintRole))


class SelectionValue:
    pass


class MemberSelection(HasTraits):
    included = Bool()
    values_for = Instance(Component)
    values = Set(Instance(SelectionValue))


class CubeRegion(HasTraits):
    included = Bool()
    member = Set(Instance(MemberSelection))

    def __contains__(self, v):
        key, value = v
        kv = self.key_values
        if key not in kv.keys():
            raise KeyError(
                'Unknown key: {0}. Allowed keys are: {1}'.format(
                    key, list(kv.keys())))
        return (value in kv[key]) == self.include


class ContentConstraint(Constraint):
    data_content_region = Instance(CubeRegion, allow_none=True)
    # metadata_content_region = Instance(MetadataTargetRegion, allow_none=True)

    def __contains__(self, v):
        if self.cube_region:
            result = [v in c for c in self.cube_region]
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
                'ContentConstraint does not contain any CubeRegion.')


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


class DataAttribute(Component):
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

    def order_key(self, key):
        """Return a key ordered according to the DSD."""
        result = Key()
        for dim in sorted(self.components, key=attrgetter('order')):
            try:
                result[dim.id] = key[dim.id]
            except KeyError:
                continue
        return result


class GroupDimensionDescriptor(DimensionDescriptor):
    attachment_constraint = Bool()
    # constraint = Instance(AttachmentConstraint, allow_none=True)


class DataStructureDefinition(Structure, ConstrainableArtefact):
    attributes = Instance(AttributeDescriptor, args=())
    dimensions = Instance(DimensionDescriptor)
    measures = Instance(MeasureDescriptor)
    group_dimensions = Instance(GroupDimensionDescriptor)

    @property
    def grouping(self):
        return


class DataflowDefinition(StructureUsage, ConstrainableArtefact):
    pass


# 5.4: Data Set

class KeyValue(HasTraits):
    id = Unicode()
    value = Any()

    def __eq__(self, other):
        """Compare the value to a Python built-in type, e.g. str."""
        return self.value == other

    def __str__(self):
        return '{0.id}: {0.value}'.format(self)


TimeKeyValue = KeyValue


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
    values = DictLikeTrait(Instance(KeyValue))
    described_by = Instance(DimensionDescriptor, allow_none=True)

    def __init__(self, arg=None, **kwargs):
        if arg:
            if len(kwargs):
                raise ValueError("Key() accepts either a single argument, or "
                                 "keyword arguments; not both.")
            kwargs.update(arg)
        for id, value in kwargs.items():
            self.values[id] = KeyValue(id=id, value=value)

    def __len__(self):
        """The length of the key is the number of KeyValues it contains."""
        return len(self.values)

    def __contains__(self, other):
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

    def __str__(self):
        return '({})'.format(', '.join(map(str, self.values.values())))

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
        return all([a == b for a, b in zip(self.values, other.values)])

    def order(self, value=None):
        if value is None:
            value = self
        try:
            return self.described_by.order_key(value)
        except AttributeError:
            return value

    def get_values(self):
        return tuple([kv.value for kv in self.values.values()])


SeriesKey = Key


class GroupKey(Key):
    id = Unicode()
    described_by = Instance(GroupDimensionDescriptor)


class AttributeValue(HasTraits):
    """SDMX-IM AttributeValue.

    In the spec, AttributeValue is an abstract class. Here, it serves as both
    the concrete subclasses CodedAttributeValue and UncodedAttributeValue.
    """
    value = Union([Unicode(), Instance(Code)])
    value_for = Instance(DataAttribute, allow_none=True)
    start_date = Instance(date)

    def __eq__(self, other):
        return self.value == other


class Observation(HasTraits):
    """SDMX-IM Observation.

    This class also implements the spec classes ObservationValue,
    UncodedObservationValue, and CodedObservation.
    """
    attrib = DictLikeTrait(Instance(AttributeValue))
    series_key = Instance(SeriesKey, allow_none=True)
    dimension = Instance(Key, allow_none=True)
    value = Union([Any(), Instance(Code)])
    value_for = Instance(PrimaryMeasure, allow_none=True)

    @property
    def dim(self):
        if len(self.key) == 1:
            return self.key.values[0]
        else:
            raise ValueError("Observations with keys of length > 1 have no "
                             "dimension.")

    @property
    def key(self):
        return self.series_key + self.dimension

    def __len__(self):
        return len(self.key)

    def __str__(self):
        return '{0.key}: {0.value}'.format(self)

    def add_attributes(self, keys, values):
        for k, v in zip(keys, values):
            self.attrib[k] = AttributeValue(value=v)


class DataSet(AnnotableArtefact):
    action = UseEnum(ActionType)
    attrib = DictLikeTrait(Instance(AttributeValue))
    valid_from = Unicode(allow_none=True)
    structured_by = Instance(DataStructureDefinition)
    obs = List(Instance(Observation))

    def add_attributes(self, keys, values):
        for k, v in zip(keys, values):
            self.attrib[k] = AttributeValue(value=v)


###############################################################################
# Message-related classes (not part of the SDMX-IM)

class Header(HasTraits):
    error = Unicode()
    id = Unicode()
    prepared = Unicode()
    receiver = Unicode()
    sender = Union([Instance(Item), Unicode()])


class Footer(HasTraits):
    severity = Unicode()
    text = List(Unicode())
    code = Int()


class Message(HasTraits):
    """Message.

    Message and its subclasses are not part of the SDMX data model.
    """
    header = Instance(Header)
    footer = Instance(Footer, allow_none=True)


class StructureMessage(Message):
    _content_types = [
        ('codelist', 'read_identifiables', Codelist, None),
        ('conceptscheme', 'read_identifiables', ConceptScheme, None),
        ('dataflow', 'read_identifiables', DataflowDefinition,
         'dataflow_from_msg'),
        ('datastructure', 'read_identifiables',
         DataStructureDefinition, None),
        ('constraint', 'read_identifiables', ContentConstraint, None),
        ('categoryscheme', 'read_identifiables', CategoryScheme, None),
        ]


class _AllDimensions:
    pass


AllDimensions = _AllDimensions()


class DataMessage(Message):
    data = List(Instance(DataSet))
    structure = Instance(DataStructureDefinition)
    observation_dimension = Union([Instance(_AllDimensions),
                                   List(Instance(Dimension))], allow_none=True)
