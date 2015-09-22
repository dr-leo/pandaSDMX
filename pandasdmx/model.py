

# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>

'''


This module is part of the pandaSDMX package

        SDMX 2.1 information model

(c) 2014 Dr. Leo (fhaxbox66@gmail.com)
'''

from .utils import DictLike, str_type
from operator import attrgetter
from collections import OrderedDict
from itertools import groupby


class SDMXObject(object):

    def __init__(self, reader, elem, **kwargs):

        object.__setattr__(self, '_reader', reader)
        object.__setattr__(self, '_elem', elem)
        super(SDMXObject, self).__init__(**kwargs)


class Message(SDMXObject):
    _payload_names = OrderedDict(
        footer='read_one')

    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        # Initialize data attributes for which the response contains payload
        for name, method in self._payload_names.items():
            value = getattr(
                self._reader, method)(name, self)
            if value:
                setattr(self, name, value)

    @property
    def header(self):
        return self._reader.read_instance(Header, self)


class StructureMessage(Message):
    _payload_names = OrderedDict(
        footer='read_one',
        codelists='read_identifiables',
        conceptschemes='read_identifiables',
        dataflows='read_identifiables',
        datastructures='read_identifiables',
        constraints='read_identifiables',
        categoryschemes='read_identifiables',
        categorisations='read_one')

    def __init__(self, *args, **kwargs):
        super(StructureMessage, self).__init__(*args, **kwargs)


class DataMessage(Message):

    def __init__(self, *args, **kwargs):
        super(DataMessage, self).__init__(*args, **kwargs)
        # Set data attribute assuming the
        # message contains at most one dataset.
        data = self._reader.read_one('data', self)
        if data:
            self.data = data


class GenericDataMessage(DataMessage):
    pass


class StructureSpecificDataMessage(DataMessage):
    pass


class Header(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Header, self).__init__(*args, **kwargs)
        # Set additional attributes present in DataSet messages
        for name in ['structured_by', 'dim_at_obs']:
            value = self._reader.read_as_str(name, self)
            if value:
                setattr(self, name, value)

    @property
    def id(self):
        return self._reader.read_as_str('headerID', self)

    @property
    def prepared(self):
        return self._reader.header_prepared(self)

    @property
    def sender(self):
        return self._reader.header_sender(self)

    @property
    def error(self):
        return self._reader.header_error(self)

    @property
    def structure(self):
        return self._reader.read_one(self._elem)


class Footer(SDMXObject):

    @property
    def text(self):
        return self._reader.footer_text(self)

    @property
    def severity(self):
        return self._reader.footer_severity(self)

    @property
    def code(self):
        return self._reader.footer_code(self)


class Constrainable:
    pass


class Annotation(SDMXObject):

    @property
    def id(self):
        return self._reader.id(self)

    @property
    def title(self):
        return self._reader.title(self)

    @property
    def annotationtype(self):
        return self._reader.read_as_str('annotationtype', self)

    @property
    def url(self):
        return self._reader.read_as_str('url', self)

    @property
    def text(self):
        return self._reader.international_str('AnnotationText', self)

    def __str__(self):
        return 'Annotation: title=%s' % self.title


class AnnotableArtefact(SDMXObject):

    @property
    def annotations(self):
        return self._reader.read_instance(Annotation, self, first_only=False)


class IdentifiableArtefact(AnnotableArtefact):

    def __init__(self, *args, **kwargs):
        super(IdentifiableArtefact, self).__init__(*args, **kwargs)
        ref = self._reader.read_instance(Ref, self)
        if ref:
            self.ref = ref
        try:
            self.id = self.ref.id
        except AttributeError:
            self.id = self._reader.read_as_str('id', self)

    def __eq__(self, value):
        if isinstance(value, str_type):
            return (self.id == value)
        else:
            raise TypeError(
                '{} not supported for comparison with IdentifiableArtefact'.format(type(value)))

    def __ne__(self, value):
        if isinstance(value, str_type):
            return (self.id != value)
        else:
            raise TypeError(
                '{} not supported for comparison with IdentifiableArtefact'.format(type(value)))

    def __hash__(self):
        return super(IdentifiableArtefact, self).__hash__()

    @property
    def urn(self):
        return self._reader.read_as_str('urn', self)

    @property
    def uri(self):
        return self._reader.read_as_str('uri', self)


class NameableArtefact(IdentifiableArtefact):

    @property
    def name(self):
        try:
            return object.__getattribute__(self, '_name')
        except AttributeError:
            object.__setattr__(
                self, '_name', self._reader.international_str('Name', self))
            return self._name

    @property
    def description(self):
        try:
            return self._description
        except AttributeError:
            self._description = self._reader.international_str(
                'description', self)
            return self._description

    def __str__(self):
        result = ' | '.join(
            (self.__class__.__name__, self.id))
        try:
            result += (' | ' + self.name.en)
        except AttributeError:
            pass
        return result

    # Make dicts and lists of Artefacts more readable. Use pprint or altrepr
    # instead?
    __repr__ = __str__


class VersionableArtefact(NameableArtefact):

    @property
    def version(self):
        return self._reader.version(self)

    @property
    def valid_from(self):
        return self._reader.valid_from(self)

    @property
    def valid_to(self):
        return self._reader.valid_to(self)


class MaintainableArtefact(VersionableArtefact):

    @property
    def is_final(self):
        return self._reader.is_final(self)

    @property
    def is_external_ref(self):
        return self._reader.is_external_ref(self)

    @property
    def structure_url(self):
        return self._reader.structure_url(self)

    @property
    def service_url(self):
        return self._reader.service_url(self)

    @property
    def maintainer(self):
        return self._reader.maintainer(self)

# Helper class for ItemScheme and ComponentList.
# This is not specifically mentioned in the SDMX info-model.
# ItemSchemes and ComponentList differ only in that ItemScheme is Nameable, whereas
# ComponentList is only identifiable. Therefore, ComponentList cannot
# inherit from ItemScheme.


class Scheme(DictLike):
    # will be passed to _reader.read_identifiables. overwrite in subclasses
    _get_items = None

    def __init__(self, *args, **kwargs):
        super(Scheme, self).__init__(*args, **kwargs)
        self._reader.read_identifiables(self._get_items, self)

    # DictLike.aslist returns a list sorted by _sort_key.
    # Alphabetical order by 'id' is the default. DimensionDescriptor overrides this
    # to sort by position.
    _sort_key = 'id'

    def aslist(self):
        return sorted(self.values(), key=attrgetter(self._sort_key))


class ItemScheme(MaintainableArtefact, Scheme):

    @property
    def is_partial(self):
        return self._reader.is_partial(self)


class Item(NameableArtefact):

    @property
    def parent(self):
        return self._reader._item_parent(self)

    @property
    def children(self):
        return self._reader._iterm_children(self)


class Structure(MaintainableArtefact):
    # the groupings are added in subclasses as class attributes.
    # This deviates from the info model
    pass


class StructureUsage(MaintainableArtefact):

    @property
    def structure(self):
        return self._reader.read_instance(Ref, self, offset='ref_structure')


class ComponentList(IdentifiableArtefact, Scheme):
    pass


class Representation(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Representation, self).__init__(*args)
        self.enum = kwargs.get('enum')

    # not_enumerated = List # of facets


class Facet:
    facet_type = {}  # for attributes such as isSequence, interval
    facet_value_type = ('String', 'Big Integer', 'Integer', 'Long',
                        'Short', 'Double', 'Boolean', 'URI', 'DateTime',
                        'Time', 'GregorianYear', 'GregorianMonth', 'GregorianDate',
                        'Day', 'MonthDay', 'Duration')
    itemscheme_facet = u''  # to be completed

    def __init__(self, facet_type=None, facet_value_type=u'',
                 itemscheme_facet=u'', *args, **kwargs):
        self.facet_type = facet_type
        self.facet_value_type = facet_value_type
        self.itemscheme_facet = itemscheme_facet


class Concept(Item):
    pass
    # core_repr = Instance(Representation)
    # iso_concept = Instance(IsoConceptReference


class Component(IdentifiableArtefact):

    @property
    def concept(self):
        return self._reader.concept_id(self)

    @property
    def local_repr(self):
        return self._reader.localrepr(self)


class Code(Item):
    pass


class Codelist(ItemScheme):
    _get_items = 'codes'


class ConceptScheme(ItemScheme):
    _get_items = 'concepts'


class Constraint(MaintainableArtefact):

    def __init__(self, *args, **kwargs):
        super(Constraint, self).__init__(*args, **kwargs)
        self.constraint_attachment = self._reader.read_subclass_instance(
            Constrainable, self, offset='constraint_attachment')[0]


class ContentConstraint(Constraint):

    def __init__(self, *args, **kwargs):
        super(ContentConstraint, self).__init__(*args, **kwargs)
        self.cube_region = self._reader.read_instance(CubeRegion, self)

    def __contains__(self, v):
        if self.cube_region:
            return v in self.cube_region
        else:
            raise NotImplementedError(
                'ContentConstraint does not contain any CubeRegion.')


class KeyValue(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(KeyValue, self).__init__(*args, **kwargs)
        self.id = self._reader.read_as_str('id', self)
        self.values = self._reader.read_as_str('value', self, first_only=False)


class CubeRegion(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(CubeRegion, self).__init__(*args, **kwargs)
        self.include = bool(self._reader.read_as_str('include', self))
        keyvalues = self._reader.read_instance(KeyValue, self,
                                               first_only=False)
        self.key_values = {kv.id: kv.values for kv in keyvalues}

    def __contains__(self, v):
        key, value = v
        kv = self.key_values
        if key not in kv.keys():
            raise KeyError(
                'Unknown key: {0}. Allowed keys are: {1}'.format(key, list(kv.keys())))
        if ((value in kv[key] and self.include) or
                (value not in kv[key] and not self.include)):
            return True
        else:
            return False


class Category(Item):
    pass


class CategoryScheme(ItemScheme):
    _get_items = 'categories'


class Categorisations(SDMXObject, DictLike):

    def __init__(self, *args, **kwargs):
        super(Categorisations, self).__init__(*args, **kwargs)
        raw = list(self._reader.categorisation_items(self))
        key_func = attrgetter('categorised_by.id')
        sorted_l = sorted(raw, key=key_func)
        result = {k: set(g) for k, g in groupby(sorted_l, key_func)}
        self.update(result)


class Ref(SDMXObject):

    @property
    def package(self):
        return self._reader.read_as_str('ref_package', self)

    @property
    def id(self):
        return self._reader.read_as_str('id', self)

    @property
    def ref_class(self):
        return self._reader.read_as_str('ref_class', self)

    @property
    def version(self):
        return self._reader.read_as_str('ref_version', self)

    @property
    def agency_id(self):
        return self._reader.read_as_str('agencyID', self)

    def resolve(self):
        pkg = getattr(self._reader.msg, self.package)
        return pkg[self.id]


class Categorisation(MaintainableArtefact):

    def __init__(self, *args, **kwargs):
        super(Categorisation, self).__init__(*args, **kwargs)
        self.categorised_by = self._reader.read_instance(
            Ref, self, offset='ref_target')
        self.artefact = self._reader.read_instance(
            Ref, self, offset='ref_source')


class DataflowDefinition(StructureUsage, Constrainable):
    pass


class DataStructureDefinition(Structure):

    def __init__(self, *args, **kwargs):
        super(DataStructureDefinition, self).__init__(*args, **kwargs)
        self.dimensions = self._reader.read_one('dimdescriptor', self)
        self.measures = self._reader.read_one('measures', self)
        self.attributes = self._reader.read_one('attributes', self)


class DimensionDescriptor(ComponentList):
    _get_items = 'dimensions'
    _sort_key = '_position'

    def __init__(self, *args, **kwargs):
        super(DimensionDescriptor, self).__init__(*args, **kwargs)
        # add time_dimension and measure_dimension to the scheme
        self._reader.read_identifiables('time_dimension', self)
        self._reader.read_identifiables('measure_dimension', self)


class PrimaryMeasure(Component):
    pass


class MeasureDescriptor(ComponentList):
    _get_items = 'measure_items'


class AttributeDescriptor(ComponentList):
    _get_items = 'attribute_items'


class DataAttribute(Component):

    @property
    def related_to(self):
        return self._reader.attr_relationship(self)

    # fix this
    # role = Instance(Concept)

    @property
    def usage_status(self):
        return self._reader.assignment_status(self)


class ReportingYearStartDay(DataAttribute):
    pass


class Dimension(Component):
    # role = Instance(Concept)

    @property
    def _position(self):
        return self._reader.position(self)


class TimeDimension(Dimension):
    pass
    # role must be None. Enforce this in future versions.


class MeasureDimension(Dimension):
    pass
    # representation: must be concept scheme and local, i.e. no
   # inheritance from concept


class DataSet(SDMXObject):

    #     reporting_begin = Any
    #     reporting_end = Any
    #     valid_from = Any
    #     valid_to = Any
    #     data_extraction_date = Any
    #     publication_year = Any
    #     publication_period = Any
    #     set_id = Unicode
    #     action = Enum(('update', 'append', 'delete'))
    #     described_by = Instance(DataflowDefinition)
    #     structured_by = Instance(DataStructureDefinition)
    #     published_by = Any
    #     attached_attribute = Any

    def __init__(self, *args, **kwargs):
        super(DataSet, self).__init__(*args, **kwargs)
        self.attrib = self._reader.series_attrib(self)
        self.groups = tuple(self.iter_groups)

    @property
    def dim_at_obs(self):
        return self._reader.read_as_str('dim_at_obs', self)

    def obs(self, with_values=True, with_attributes=True):
        '''
        return an iterator over observations in a flat dataset.
        An observation is represented as a namedtuple with 3 fields ('key', 'value', 'attrib').

        obs.key is a namedtuple of dimensions. Its field names represent dimension names,
        its values the dimension values.

        obs.value is a string that can in in most cases be interpreted as float64
        obs.attrib is a namedtuple of attribute names and values.

        with_values and with_attributes: If one or both of these flags
        is False, the respective value will be None. Use these flags to
        increase performance. The flags default to True.
        '''
        # distinguish between generic and structure-specific observations
        # only generic ones are currently implemented.
        if isinstance(self, GenericDataSet):
            return self._reader.iter_generic_obs(
                self, with_values, with_attributes)
        else:
            raise NotImplemented(
                'StructureSpecificDataSets are not yet supported.')

    @property
    def series(self):
        '''
        return an iterator over Series instances in this DataSet.
        Note that DataSets in flat format, i.e.
        header.dim_at_obs = "AllDimensions", have no series. Use DataSet.obs() instead.
        '''
        return self._reader.generic_series(self)

    @property
    def iter_groups(self):
        return self._reader.generic_groups(self)


class StructureSpecificDataSet(DataSet):
    pass


class GenericDataSet(DataSet):
    pass


class Series(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Series, self).__init__(*args)
        self.key = self._reader.series_key(self)
        self.attrib = self._reader.series_attrib(self)
        dataset = kwargs.get('dataset')
        if not isinstance(dataset, DataSet):
            raise TypeError("'dataset' must be a DataSet instance, got %s"
                            % dataset.__class__.__name__)
        self.dataset = dataset

    @property
    def group_attrib(self):
        '''
        return a namedtuple containing all attributes attached
        to groups of which the given series is a member
        for each group of which the series is a member
        '''
        g_attrib = DictLike()
        for g in self.dataset.groups:
            if self in g:
                g_attrib.update(g.attrib)
        return g_attrib

    def obs(self, with_values=True, with_attributes=True, reverse_obs=False):
        '''
        return an iterator over observations in a series.
        An observation is represented as a namedtuple with 3 fields ('key', 'value', 'attrib').
        obs.key is a namedtuple of dimensions, obs.value is a string value and
        obs.attrib is a namedtuple of attributes. If with_values or with_attributes
        is False, the respective value is None. Use these flags to
        increase performance. The flags default to True.
        '''
        return self._reader.iter_generic_series_obs(self,
                                                    with_values, with_attributes, reverse_obs)


class Group(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        self.key = self._reader.group_key(self)
        self.attrib = self._reader.series_attrib(self)

    def __contains__(self, series):
        group_key, series_key = self.key, series.key
        for f in group_key._fields:
            if getattr(group_key, f) != getattr(series_key, f):
                return False
        return True
