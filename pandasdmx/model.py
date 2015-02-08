

'''


This module is part of the pandaSDMX package

        SDMX 2.1 information model

(c) 2014 Dr. Leo (fhaxbox66@gmail.com)
'''

from .utils    import DictLike, str_type
from IPython.utils.traitlets import (HasTraits, Unicode, Instance, List, 
            Any, Enum, Dict)
from operator import attrgetter 


class SDMXObject(object):
    def __init__(self, reader, elem, **kwargs):
        
        object.__setattr__(self, '_reader', reader)
        object.__setattr__(self, '_elem', elem)
        super(SDMXObject, self).__init__(**kwargs)
        
      
class Message(SDMXObject):
    _payload_names = ['footer']
    
    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        # Initialize data attributes for which the response contains payload
        for name in self._payload_names:
            try:
                getattr(self, name)
            except ValueError: pass 
        
    def __getattr__(self, name):
        if name in self._payload_names:
            value = self._reader.read_identifiables(name, self)
            if value:
                setattr(self, name, value) 
                return value
            else:
                raise ValueError(
                                    'SDMX response does not containe any payload of type %s.' 
                                    % name)
        else:
            raise KeyError('{0} is not a valid payload or other attribute name.'.format(name)) 
            
            
    @property
    def header(self):
        return self._reader.read_one('header', self)
    
    
class StructureMessage(Message):
    
    def __init__(self, *args, **kwargs):
        super(StructureMessage, self).__init__(*args, **kwargs) 
        self._payload_names.extend(['codelists', 'conceptschemes', 'dataflows', 
                        'datastructures', 'categoryschemes'])


class DataMessage(Message):
    
    def __init__(self, *args, **kwargs):
        super(DataMessage, self).__init__(*args, **kwargs)
        # Set data attribute assuming the 
        # message contains at most one dataset.
        data = self._reader.read_one('data', self)
        if data: self.data = data  
            


class GenericDataMessage(DataMessage): pass
class StructureSpecificDataMessage(DataMessage): pass


class Header(SDMXObject):
    def __init__(self, *args, **kwargs):
        super(Header, self).__init__(*args, **kwargs)
        # Set additional attributes present in DataSet messages
        for name in ['structured_by', 'dim_at_obs']: 
            value = self._reader.read_one(name, self)
            if value: setattr(self, name, value)
        
    
    @property
    def id(self):
        return self._reader.header_id(self)
    
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
    def id(self):
        return self._reader.header_id(self)
    
    @property
    def prepared(self):
        return self._reader.header_prepared(self) 

    @property
    def sender(self):
        return self._reader.header_sender(self) 

        
class Annotation(SDMXObject):
    
    @property
    def id(self): 
        return self._reader.id(self)
    
    @property
    def title(self):
        return self._reader.title(self)
    
    @property
    def annotationtype(self):
        return self._reader.read_one('annotationtype', self)
    
    @property
    def url(self):
        return self._reader.url(self)
    @property
    def text(self):
        return self._reader.international_str('AnnotationText', self)
        
    def __str__(self):
        return 'Annotation: title=%s' , self.title  


class AnnotableArtefact(SDMXObject):
    @property
    def annotations(self):
        return self._reader.read_iter('annotations', self)
    
        
class IdentifiableArtefact(AnnotableArtefact):
    @property
    def id(self):
        return self._reader.identity(self)

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
        return self._reader.urn(self)
    
    @property
    def uri(self):
        return self._reader.uri(self)
    
    
class NameableArtefact(IdentifiableArtefact):
    @property
    def name(self):
        return self._reader.international_str('Name', self)
    
    @property
    def description(self):
        return self._reader.international_str('Description', self)    
    
    def __str__(self):
        return ' '.join((self.__class__.__name__, ':', self.id, ' :', self.name.en))
    
    # Make dicts and lists of Artefacts more readable. Use pprint or altrepr instead? 
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
    _get_items = None # subclasses must set this to the name of the reader method 
    
    def __init__(self, *args, **kwargs):
        super(Scheme, self).__init__(*args, **kwargs)
        self._reader.read_identifiables(self._get_items, self)
    
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
        return self._reader.structure(self) 
    
    
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
        return self._reader.concept_id(self)
    
    @property
    def local_repr(self):
        return self._reader.localrepr(self)

class Code(Item): pass

class Codelist(ItemScheme):
    
    _get_items = 'codes'
    

class ConceptScheme(ItemScheme):
    _get_items = 'concepts'
     

class Category(Item): pass

class CategoryScheme(ItemScheme):
    _get_items = 'categories'

    

class Categorisation(MaintainableArtefact):
    artefact = Instance(IdentifiableArtefact)
    categorized_by = Instance(Category)
    
        
class IdentifiableObjectType: pass
class ConstraintRoleType: pass    


class DataflowDefinition(StructureUsage): pass 
     

class DataStructureDefinition(Structure):
    def __init__(self, *args, **kwargs):
        super(DataStructureDefinition, self).__init__(*args, **kwargs)
        self.dimensions= self._reader.read_one('dimdescriptor', self)
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
        
    
class DimensionRelationship(GroupRelationship):
    dimensions = List # of dimensions
    
        
class DataAttribute(Component):
    
    @property
    def related_to(self):
        return self._reader.attr_relationship(self)  
    
    # fix this
    # role = Instance(Concept)  
    
    @property
    def usage_status(self):
        return self._reader.assignment_status(self)
    
    
    
class ReportingYearStartDay(DataAttribute): pass


class Dimension(Component):   
    # role = Instance(Concept)
    
    @property
    def _position(self):
        return self._reader.position(self)

class TimeDimension(Dimension): pass 
    # role must be None. Enforce this in future versions.

class MeasureDimension(Dimension): pass 
    # representation: must be concept scheme and local, i.e. no
    # inheritance from concept


class HasObservations:
    '''
    Base class for DataSets and series. Both may have observations.
    '''    
    def obs(self, with_values = True, with_attributes = False):
        '''
        return an iterator over observations in a flat dataset or series.
        An observation is represented as a triple if         with_values and with_attributes are both set to True.
        In this case obs[0] is a namedtuple of dimensions, obs[1] is a string value and
        obs[2] is a namedtuple of attributes. If with_values or with_attributes
        is False, the respective value is None. Use these flags to
        increase performance. 
        '''
        # distinguish between generic and structure-specific observations
        # only generic ones are currently implemented.
        if isinstance(self, GenericDataSet):
            return self._reader.iter_generic_obs(self, with_values, with_attributes)
        else: raise NotImplemented('StructureSpecificDataSets are not supported.')
            
    
    
class DataSet(SDMXObject, HasObservations):
    
    
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
        
        
    
    
class StructureSpecificDataSet(DataSet): pass
 
class GenericDataSet(DataSet): pass

 

class Key:
    key_values = List
    attached_attribute = Any

class KeyValue: pass


class SeriesKey(Key): pass
class GroupKey(Key): pass

