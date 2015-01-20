

'''


This module is part of the pandaSDMX package

        SDMX 2.1 information model

(c) 2014 Dr. Leo (fhaxbox66@gmail.com)
'''

from pandasdmx.utils    import DictLike, str_type
from IPython.utils.traitlets import (HasTraits, Unicode, Instance, List, 
            Any, Enum, Dict)
from operator import attrgetter 


class SDMXObject(object):
    def __init__(self, reader, elem, **kwargs):
        
        object.__setattr__(self, '_reader', reader)
        object.__setattr__(self, '_elem', elem)
        super(SDMXObject, self).__init__(**kwargs)
        
      
class Response(SDMXObject):
    
    _structure_names = ['codelists', 'conceptschemes', 'dataflows', 'datastructures']
    
    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)
        # Initialize data attributes for which the response contains payload
        for name in self._structure_names:
            try:
                getattr(self, name)
            except ValueError: pass 
        
    def __getattr__(self, name):
        if name in self._structure_names:
            value = getattr(self._reader, name)(self._elem)
            if value:
                setattr(self, name, value) 
                return value
            else:
                raise ValueError(
                    'SDMX response does not containe any payload of type %s.' 
                    % name)
        else:
            raise AttributeError('{0} not found.'.format(name)) 
            
            
            
    @property
    def header(self):
        return self._reader.mes_header(self._elem)
    

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
    
    def __init__(self,  **kwargs):
        super(InternationalString, self).__init__( **kwargs)
    
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
    
        
class IdentifiableArtefact(AnnotableArtefact):
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
    
    def __str__(self):
        return ' '.join((self.__class__.__name__, 'ID:', self.id, 'name:', self.name.en))
    
    
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
    
# Helper class for ItemScheme and ComponentList. 
# This is not specifically mentioned in the SDMX info-model. 
# ItemSchemes and ComponentList differ only in that ItemScheme is Nameable, whereas
# ComponentList is only identifiable. Therefore, ComponentList cannot
# inherit from ItemScheme.     
class Scheme(DictLike):
    _get_items = None # subclasses must set this to the name of the reader method 
    
    def __init__(self, *args, **kwargs):
        super(Scheme, self).__init__(*args, **kwargs)
        self.update(getattr(self._reader, self._get_items)(self._elem))
    
    def find(self, search_str, by = 'name', language = 'en'):
        '''
        return new DictLike of items where value.<by> contains the search_str. 'by' defaults to 'name'. 
        If the <by> attribute is an international string,
        'language' (defaults to 'en') is used to select the desired language. self.values() should therefore contain model.NameableArtefact subclass instances.
        Any capitalization is disregarded. Hence 'a' == 'A'.
        '''
        s = search_str.lower()
        # We distinguish between international strings stored as dict such as 
        # name.en, name.fr, and normal strings.
        if by in ['name', 'description']:
            get_field = lambda obj: getattr(obj, by)[language]
        else: # normal string
            get_field = lambda obj: getattr(obj, by)
        return DictLike(result for result in self.items() 
                        if s in get_field(result[1]).lower())
    
    # DictLike.aslist returns a list sorted by _sort_key. 
    # Alphabetical order by 'id' is the default. DimensionDescriptor overrides this 
    # to sort by position. 
    _sort_key = 'id'
    @property
    def aslist(self):
        return sorted(self.values(), key = attrgetter(self._sort_key)) 
        
    
class ItemScheme(MaintainableArtefact, Scheme):
    
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
    
    @property
    def structure(self):
        return self._reader.structure(self._elem) 
    
    
class ComponentList(IdentifiableArtefact, Scheme): pass
        

class Representation(SDMXObject):
    def __init__(self, *args, enum = None, **kwargs):
        super(Representation, self).__init__(*args)
        self.enum = enum
    
    # not_enumerated = List # of facets
        
        
class Facet(HasTraits):
    facet_type = Dict # for attributes such as isSequence, interval 
    facet_value_type = Enum(('String', 'Big Integer', 'Integer', 'Long',
                            'Short', 'Double', 'Boolean', 'URI', 'DateTime', 
                'Time', 'GregorianYear', 'GregorianMonth', 'GregorianDate', 
                'Day', 'MonthDay', 'Duration'))
    itemscheme_facet = Unicode # to be completed
    
    def __init__(self, facet_type = None, facet_value_type = u'', 
                 itemscheme_facet = u'', *args, **kwargs):
        super(Facet, self).__init__(*args, **kwargs)
        self.facet_type = facet_type
        self.facet_value_type = facet_value_type
        self.itemscheme_facet = itemschemefacet
               
        
class IsoConceptReference: pass # to be completed

class Concept(Item): pass
    # core_repr = Instance(Representation)
    # iso_concept = Instance(IsoConceptReference) 
        
    
class Component(IdentifiableArtefact):
    
    @property
    def concept(self):
        return self._reader.concept_id(self._elem)
    
    @property
    def local_repr(self):
        return self._reader.localrepr(self._elem)

class Code(Item): pass

class Codelist(ItemScheme):
    
    _get_items = 'codes'
    

class ConceptScheme(ItemScheme):
    _get_items = 'concepts'
     

class Category(Item): pass

class CategoryScheme(ItemScheme):
    _get_items = 'categories'

    

class Categorization(MaintainableArtefact):
    artefact = Instance(IdentifiableArtefact)
    categorized_by = Instance(Category)
    
    def __init__(self, id_artefact, category,  **kwargs):
        super(Categorization, self).__init__( **kwargs)
        self.artefact = id_artefact
        self.categorized_by = category
        
class IdentifiableObjectType: pass
class ConstraintRoleType: pass    


class DataflowDefinition(StructureUsage): pass 
     

class DataStructureDefinition(Structure):
    def __init__(self, *args, **kwargs):
        super(DataStructureDefinition, self).__init__(*args, **kwargs)
        self.dimensions= self._reader.dimdescriptor(self._elem)
        self.measures = self._reader.measures(self._elem)
        self.attributes = self._reader.attributes(self._elem)


class DimensionDescriptor(ComponentList):
    _get_items = 'dimension_items'
    _sort_key = '_position'
    
    
class GroupDimensionDescriptor(ComponentList):
    # Associations to dimension etc. are not distinguished from
    # the actual dimensions. This differs technically from the model specification
    dimension = Instance(Component)
    measure_dimension = Instance(Component)
    time_dimension = Instance(Component)
    # constraint to be added
    
        
class PrimaryMeasure(Component): pass

class MeasureDescriptor(ComponentList):
    _get_items = 'measure_items'
    

class AttributeDescriptor(ComponentList): 
    _get_items = 'attribute_items'
    
    
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
    
    @property
    def related_to(self):
        return self._reader.attr_relation(self._elem)  
    
    
    # role = Instance(Concept)
    
    @property
    def usage_status(self):
        return self._reader.assignment_status(self._elem)
    
    
    
class ReportingYearStartDay(DataAttribute): pass


class Dimension(Component):   
    # role = Instance(Concept)
    
    @property
    def _position(self):
        return self._reader.position(self._elem)

class TimeDimension(Dimension): pass 
    # role must be None. Enforce this in future versions.

class MeasureDimension(Dimension): pass 
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

