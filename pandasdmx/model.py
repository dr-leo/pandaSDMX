

'''


This module is part of the pandaSDMX package

SDMX 2.1 information model

(c) 2014 Dr. Leo (fhaxbox66@gmail.com)
'''

from pandasdmx.utils    import HasItems, DictLike, str_type
from IPython.utils.traitlets import (HasTraits, Unicode, Instance, List, Bool, 
            Any, This, Enum, Dict)


class SDMXObject:
    def __init__(self, reader, elem, **kwargs):
        self._reader = reader
        self._elem = elem
        super(SDMXObject, self).__init__(**kwargs)
      
class Message(SDMXObject):
            
    @property
    def header(self):
        return self._reader.mes_header(self._elem)
    
    @property
    def codelists(self):
        return self._reader.codelists(self._elem)

    @property
    def concept_schemes(self):
        return self._reader.concept_schemes(self._elem)
        
        
class Header(SDMXObject):
    @property
    def id(self):
        return self._reader.header_id(self._elem)
    
    @property
    def prepared(self):
        return self._reader.header_prepared(self._elem) 

    @property
    def sender(self):
        return self._reader.header_sender(self._elem) 

    @property
    def error(self):
        return self._reader.header_error(self._elem) 



class InternationalString(DictLike):
    
    def __init__(self, *args, **kwargs):
        super(InternationalString, self).__init__(*args, **kwargs)
    
    def get_locales(self): return self.keys()
    
    def get_labels(self): return self.values()
    
        
class Annotation(SDMXObject):
    @property
    def id(self): 
        return self._reader.id(self._elem)
    @property
    def title(self):
        return self._reader.title(self._elem)
    @property
    def annotype(self):
        return self._reader.annotationtype(self._elem)
    @property
    def url(self):
        return self._reader.url(self._elem)
    @property
    def text(self):
        return self._reader.text(self._elem)
        
    def __str__(self):
        return 'Annotation: title=%s' , self.title  


class AnnotableArtefact(SDMXObject):
    @property
    def annotations(self):
        return self._reader.annotations(self._elem)
    
        
class IdentifiableArtefact(SDMXObject):
    @property
    def id(self):
        return self._reader.identity(self._elem)

    def __eq__(self, value):
        if isinstance(value, str_type):
            return (self.id == value)
        else: raise TypeError('{} not supported for comparison with IdentifiableArtefact'.format(type(value)))

    def __ne__(self, value):
        if isinstance(value, str_type):
            return (self.id != value)
        else: raise TypeError('{} not supported for comparison with IdentifiableArtefact'.format(type(value)))

    def __hash__(self): 
        return super(IdentifiableArtefact, self).__hash__()
    
    @property
    def urn(self):
        return self._reader.urn(self._elem)
    
    @property
    def uri(self):
        return self._reader.uri(self._elem)
    
    
class NameableArtefact(IdentifiableArtefact):
    @property
    def name(self):
        return self._reader.name(self._elem)
    
    @property
    def description(self):
        return self._reader.description(self._elem)    
    
    
class VersionableArtefact(NameableArtefact):

    @property
    def version(self):
        return self._reader.version(self._elem)
    
    @property
    def valid_from(self):
        return self._reader.valid_from(self._elem)
    
    @property
    def valid_to(self):
        return self._reader.valid_to(self._elem)
    

class MaintainableArtefact(VersionableArtefact):
    
    @property
    def is_final(self):
        return self._reader.is_final(self._elem)
    
    @property
    def is_external_ref(self):
        return self._reader.is_external_ref(self._elem)
    
    @property
    def structure_url(self):
        return self._reader.structure_url(self._elem)
    
    @property
    def service_url(self):
        return self._reader.service_url(self._elem)
    
    @property
    def maintainer(self):
        return self._reader.maintainer(self._elem)
    
    
class ItemScheme(MaintainableArtefact, HasItems): 
    
    @property
    def is_partial(self):
        return self._reader.is_partial(self._elem)
    
    
         
         
class Item(NameableArtefact):
    
    @property       
    def parent(self):
        return self._reader._item_parent(self._elem)
    
    @property
    def children(self):
        return self._reader._iterm_children(self._elem) 
    

class Structure(MaintainableArtefact):
    # the groupings are added in subclasses as class attributes. 
    # This deviates from the info model
    pass

class StructureUsage(MaintainableArtefact):
    struct = Instance(Structure)
    
    def __init__(self, structure = None, *args, **kwargs):
        super(StructureUsage, self).__init__(*args, **kwargs)
        self.struct = structure
    
    
class Componentlist(IdentifiableArtefact, IsIterable): pass
# Components are passed through the items attribute required by the IsIterable superclass.
# The 'components' attribute foreseen in the model is thus omitted. 


class Representation(SDMXObject):
    enumerated = Instance(ItemScheme)
    not_enumerated = List # of facets
        
        
class Facet(HasTraits):
    facet_type = Dict # for attributes such as isSequence, interval 
    facet_value_type = Enum(('String', 'Big Integer', 'Integer', 'Long',
                            'Short', 'Double', 'Boolean', 'URI', 'DateTime', 
                'Time', 'GregorianYear', 'GregorianMonth', 'GregorianDate', 
                'Day', 'MonthDay', 'Duration'))
    itemscheme_facet = Unicode # to be completed
    
    def __init__(self, *args, facet_type = None, facet_value_type = u'', 
                 itemscheme_facet = u'', **kwargs):
        super(Facet, self).__init__(*args, **kwargs)
        self.facet_type = facet_type
        self.facet_value_type = facet_value_type
        self.itemscheme_facet = itemschemefacet
               
        
class IsoConceptReference: pass # to be completed

class Concept(Item): pass
    # core_repr = Instance(Representation)
    # iso_concept = Instance(IsoConceptReference) 
        
    
class Component(IdentifiableArtefact):
    concept_id = Instance(Concept)
    local_repr = Instance(Representation)

    def __init__(self, *args, concept_id =None, local_repr =None, **kwargs):
        super(Component, self).__init__(*args, **kwargs)
        self.concept_id = concept_id
        self.local_repr = local_repr
        
class Code(Item): pass

class Codelist(ItemScheme):
    
    @property
    def items_by_slice(self, items): # to be reviewed
        return self._reader.codes_by_slice(s)
        
        return self._reader.iter_codes(self._elem)



class ConceptScheme(ItemScheme):
    @property
    def items(self):
        return self._reader.iter_concepts(self._elem)
     

class Category(Item): pass
class CategoryScheme(ItemScheme):
    child_cls = Category



class Categorization(MaintainableArtefact):
    artefact = Instance(IdentifiableArtefact)
    categorized_by = Instance(Category)
    
    def __init__(self, id_artefact, category, *args, **kwargs):
        super(Categorization, self).__init__(*args, **kwargs)
        self.artefact = id_artefact
        self.categorized_by = category
        
class IdentifiableObjectType: pass
class ConstraintRoleType: pass    


class DataflowDefinition(StructureUsage): pass 
     

class DataStructureDefinition(Structure):
    grouping = Any
    def __init__(self, *args, grouping = u'', **kwargs):
        super(DataStructureDefinition, self).__init__(*args, **kwargs)
        self.grouping = grouping
        
        
class GroupDimensionDescriptor(Componentlist):
    constraint = Any
    
    def __init__(self, *args, constraint = u'', components = u'', **kwargs):
        super(GroupDimensionDescriptor, self).__init__(*args, **kwargs)
        self.constraint = constraint
        self.components = components # not understood. Assign to self._items?


class DimensionDescriptor(Componentlist):
    dimension = Instance(Component)
    measure_dimension = Instance(Component)
    time_dimension = Instance(Component)
    
    def __init__(self, *args, dimension =None, measure_dimension =None,
                time_dimension =None, **kwargs):
        super(DimensionDescriptor, self).__init__(*args, **kwargs)
        self.dimension = dimension
        self.measure_dimension = measure_dimension
        self.time_dimension = time_dimension
        
class DimensionGroupDescriptor(Componentlist):
    # Associations to dimension etc. are not distinguished from
    # the actual dimensions. This differs technically from the model specification
    dimension = Instance(Component)
    measure_dimension = Instance(Component)
    time_dimension = Instance(Component)
    
    def __init__(self, *args, dimension =None, measure_dimension =None, 
                 time_dimension =None, **kwargs):
        super(DimensionGroupDescriptor, self).__init__(*args, **kwargs)
        self.dimension = dimension
        self.measure_dimension = measure_dimension
        self.time_dimension = time_dimension
        
class PrimaryMeasure(Component): pass

class MeasureDescriptor(Componentlist):
    primary_measure = Instance(PrimaryMeasure)
    
    def __init__(self, *args, primary_measure =None, **kwargs):
        super(MeasureDescriptor, self).__init__(*args, **kwargs)
        self.primary_measure = primary_measure

class AttributeDescriptor(Componentlist): pass
    
class AttributeRelationship: pass
class NoSpecifiedRelationship(AttributeRelationship): pass
class PrimaryMeasureRelationship(AttributeRelationship): pass


class GroupRelationship(AttributeRelationship):
    groupkey = Instance(GroupDimensionDescriptor)
    
    def __init__(self, groupkey = None):
        super().__init__()
        self.groupkey = groupkey
        
    
class DimensionRelationship(GroupRelationship):
    dimensions = List # of dimensions
    
    def __init__(self, dimensions = [], **kwargs):
        super().__init__(**kwargs)
        self.dimensions = dimensions
        
        
class DataAttribute(Component):
    related_to = Instance(AttributeRelationship)  
    role = Instance(Concept)
    usage_status = Enum(('mandatory', 'conditional')) # generalise this through constraint?
    
    def __init__(self, *args, role =None, related_to = None, **kwargs):
        super(DataAttribute, self).__init__(*args, **kwargs)
        self.related_to = related_to
        self.role = role

class ReportingYearStartDay(DataAttribute): pass


class DimensionComponent(Component): # rename this to Dimension? 
    role = Instance(Concept)
    
    def __init__(self, *args, role =None, **kwargs):
        super(DimensionComponent, self).__init__(*args, **kwargs)
        self.role = role


class TimeDimension(DimensionComponent): pass 
    # role must be None. Enforce this in future versions.

class MeasureDimension(DimensionComponent): pass 
    # representation: must be concept scheme and local, i.e. no
    # inheritance from concept
    
    
class DataSet(HasTraits):
    reporting_begin = Any 
    reporting_end = Any
    valid_from = Any
    valid_to = Any
    data_extraction_date = Any
    publication_year = Any
    publication_period = Any
    set_id = Unicode
    action = Enum(('update', 'append', 'delete'))
    described_by = Instance(DataflowDefinition)
    structured_by = Instance(DataStructureDefinition)
    published_by = Any
    attached_attribute = Any
    
    def __init__(self, reporting_begin = None, 
                 reporting_end = None,
                 valid_from = None,
                 valid_to = None,
                 data_extraction_date = None,
                 publication_year = None,
                 publication_period = None,
                 set_id = u'',
                 action = None,
                 described_by = None,
                 structured_by = None,
                 published_by = None,
                 attached_attribute = None):
        super(DataSet, self).__init__()
        self.reporting_begin = reporting_begin  
        self.reporting_end = reporting_end 
        self.valid_from = valid_from 
        self.valid_to = valid_to 
        self.data_extraction_date = data_extraction_date 
        self.publication_year = publication_year 
        self.publication_period = publication_period 
        self.set_id = set_id 
        self.action = action
        self.described_by = described_by 
        self.structured_by = structured_by 
        self.published_by = published_by 
        self.attached_attribute = attached_attribute 
    

    
class StructureSpecificDataSet(DataSet): pass
 
class GenericDataSet(DataSet): pass

class GenericTimeSeriesDataSet(DataSet): pass 
 
class StructureSpecificTimeSeriesDataSet(DataSet): pass

class Key:
    key_values = List
    attached_attribute = Any
    
    def __init__(self, key_balues = [], 
            attached_attribute = None):
        self.key_values = key_values
        self.attached_attribute = attached_attribute

class KeyValue: pass


class SeriesKey(Key): pass
class GroupKey(Key): pass

