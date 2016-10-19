
# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>

'''


This module is part of the pandaSDMX package

        SDMX 2.1 information model

(c) 2014 Dr. Leo (fhaxbox66@gmail.com)
'''

from pandasdmx.utils import DictLike, concat_namedtuples
from operator import attrgetter
from collections import defaultdict


class SDMXObject(object):

    def __init__(self, reader, elem, **kwargs):

        object.__setattr__(self, '_reader', reader)
        object.__setattr__(self, '_elem', elem)
        super(SDMXObject, self).__init__(**kwargs)


class Header(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Header, self).__init__(*args, **kwargs)
        # Set additional attributes present in DataSet messages
        for name in ['structured_by', 'dim_at_obs']:
            value = getattr(self._reader, name)(self)
            if value:
                setattr(self, name, value)

    @property
    def id(self):
        return self._reader.read_as_str('headerID', self)

    @property
    def prepared(self):
        return self._reader.read_as_str('header_prepared', self)

    @property
    def sender(self):
        return self._reader.read_as_str('header_sender', self)

    @property
    def receiver(self):
        return self._reader.read_as_str('header_receiver', self)

    @property
    def error(self):
        return self._reader.read_as_str('error', self)


class Footer(SDMXObject):

    @property
    def text(self):
        return self._reader.read_as_str('footer_text', self, first_only=False)

    @property
    def severity(self):
        return self._reader.read_as_str('footer_severity', self)

    @property
    def code(self):
        return int(self._reader.read_as_str('footer_code', self))


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
        self.urn = self._reader.read_as_str('urn', self)
        if ref:
            self.ref = ref
        try:
            self.id = self.ref.id
        except AttributeError:
            self.id = self._reader.read_as_str('id', self)

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
        return hash(self.urn)

    @property
    def uri(self):
        return self._reader.read_as_str('uri', self)

    def __repr__(self):
        result = ' | '.join(
            (self.__class__.__name__, self.id))
        return result


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
        return bool(self._reader.read_as_str('isfinal', self))

    @property
    def is_external_ref(self):
        return self._reader.is_external_ref(self)  # fix this

    @property
    def structure_url(self):
        return self._reader.structure_url(self)  # fix this

    @property
    def service_url(self):
        return self._reader.service_url(self)  # fix this

    @property
    def maintainer(self):
        return self._reader.maintainer(self)  # fix this


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
    _sort_key = attrgetter('id')

    def aslist(self):
        return sorted(self.values(), key=self._sort_key)


class ItemScheme(MaintainableArtefact, Scheme):

    @property
    def is_partial(self):
        return self._reader.is_partial(self)


class Item(NameableArtefact):

    @property
    def children(self):
        return self._reader._item_children(self)


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
        enum = self._reader.read_instance(
            Ref, self, offset='enumeration')
        if enum:
            self.text_type = self.max_length = None
            self.enum = self._reader.message.codelist[enum.id]
        else:
            self.enum = None
            self.text_type = self._reader.read_as_str('texttype', self)
            max_length = self._reader.read_as_str('maxlength', self)
            if max_length:
                self.max_length = int(max_length)
            else:
                self.max_length = None


class Facet:
    # This is not yet working. not used so far.

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

    @property  # not working yet
    def concept_identity(self):
        return self._reader.read_instance(Ref, self, offset='concept_identity')

    @property
    def concept(self):
        concept_id = self.concept_identity.id
        parent_id = self.concept_identity.maintainable_parent_id
        return self._reader.message.conceptscheme[parent_id][concept_id]

    @property
    def local_repr(self):
        return self._reader.read_instance(Representation, self)


class Code(Item):
    pass


class Codelist(ItemScheme):
    _get_items = Code


class ConceptScheme(ItemScheme):
    _get_items = Concept


class Constraint(MaintainableArtefact):

    def __init__(self, *args, **kwargs):
        super(Constraint, self).__init__(*args, **kwargs)
        self.constraint_attachment = self._reader.read_instance(
            DataflowDefinition, self, offset='constraint_attachment')


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
        return (value in kv[key]) == self.include


class Category(Item):

    def __iter__(self):
        '''
        Return an iterator over the categorised objects
        '''
        m = self._reader.message
        # We assume that only dataflow definitions are categorised.
        resource = m.dataflow
        idx = (self._reader.read_as_str('cat_scheme_id', self), self.id)
        return (resource[c.artefact.id] for c in m._categorisation[idx])


class CategoryScheme(ItemScheme):
    _get_items = Category


class Categorisations(SDMXObject, DictLike):

    def __init__(self, *args, **kwargs):
        super(Categorisations, self).__init__(*args, **kwargs)
        # Group categorisations by categoryscheme id and category id
        # Each group is represented by a list.
        result = defaultdict(list)
        for c in self._reader.read_instance(
                Categorisation, self, first_only=False):
            key = (c.categorised_by.maintainable_parent_id,
                   c.categorised_by.id)
            result[key].append(c)
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

    @property
    def maintainable_parent_id(self):
        return self._reader.read_as_str('maintainable_parent_id', self)

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


class DataAttribute(Component):

    @property
    def related_to(self):
        return self._reader.read_instance(Ref, self).id

    # fix this
    # role = Instance(Concept)

    @property
    def usage_status(self):
        return self._reader.read_as_str('assignment_status', self)


class DataStructureDefinition(Structure):

    def __init__(self, *args, **kwargs):
        super(DataStructureDefinition, self).__init__(*args, **kwargs)
        self.dimensions = self._reader.read_instance(DimensionDescriptor, self)
        self.measures = self._reader.read_instance(MeasureDescriptor, self)
        self.attributes = self._reader.read_instance(AttributeDescriptor, self)


class Dimension(Component):
    # role = Instance(Concept)

    def __init__(self, *args, **kwargs):
        super(Dimension, self).__init__(*args, **kwargs)
        self._position = int(self._reader.read_as_str('position', self))


class TimeDimension(Dimension):
    pass
    # role must be None. Enforce this in future versions.


class MeasureDimension(Dimension):
    pass
    # representation: must be concept scheme and local, i.e. no
    # inheritance from concept


class DimensionDescriptor(ComponentList):
    _get_items = Dimension
    _sort_key = attrgetter('_position')

    def __init__(self, *args, **kwargs):
        super(DimensionDescriptor, self).__init__(*args, **kwargs)
        # add time_dimension and measure_dimension to the scheme
        self._reader.read_identifiables(TimeDimension, self)
        self._reader.read_identifiables(MeasureDimension, self)


class PrimaryMeasure(Component):
    pass


class MeasureDescriptor(ComponentList):
    _get_items = PrimaryMeasure


class AttributeDescriptor(ComponentList):
    _get_items = DataAttribute


class ReportingYearStartDay(DataAttribute):
    pass


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
        self.attrib = self._reader.dataset_attrib(self)
        self.groups = tuple(self.iter_groups)

    @property
    def dim_at_obs(self):
        return self._reader.dim_at_obs(self)

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
        return self._reader.iter_generic_obs(
            self, with_values, with_attributes)

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
        group_attributes = [g.attrib for g in self.dataset.groups if self in g]
        if group_attributes:
            return concat_namedtuples(*group_attributes)

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


class Message(SDMXObject):
    # Describe supported message content as 4-tuples of the form
    # (attribute_name, reader_method_name,
    # class_object_to_be_instantiated, optional_offset_path_name)
    _content_types = [
        ('header', 'read_instance', Header, None),
        ('footer', 'read_instance', Footer, None)]

    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        # Initialize data attributes for which the response contains payload
        for name, method, cls, offset in self._content_types:
            payload = getattr(
                self._reader, method)(cls, self, offset=offset)
            if payload:
                setattr(self, name, payload)


class StructureMessage(Message):
    _content_types = Message._content_types[:]
    _content_types.extend([
        ('codelist', 'read_identifiables', Codelist, None),
        ('conceptscheme', 'read_identifiables', ConceptScheme, None),
        ('dataflow', 'read_identifiables', DataflowDefinition,
         'dataflow_from_msg'),
        ('datastructure', 'read_identifiables',
         DataStructureDefinition, None),
        ('constraint', 'read_identifiables', ContentConstraint, None),
        ('categoryscheme', 'read_identifiables', CategoryScheme, None),
        ('_categorisation', 'read_instance', Categorisations, None)])

    def __getattr__(self, name):
        '''
        Some attributes have been renamed in v0.4.
        Old names are deprecated.
        This method ensures backward compatibility. It will be
        removed in a future version.
        '''
        old2new = {
            'codelists': 'codelist',
            'dataflows': 'dataflow',
            'categoryschemes': 'categoryscheme',
            'categorisations': 'categorisation',
            'conceptschemes': 'conceptscheme',
            'datastructures': 'datastructure'}
        if name in old2new:
            return getattr(self, old2new[name])
        else:
            raise AttributeError


class DataMessage(Message):
    _content_types = Message._content_types[:]
    _content_types.extend([
        ('data', 'read_instance', DataSet, None)])
