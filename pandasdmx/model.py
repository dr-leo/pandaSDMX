

'''


This module is part of the pandaSDMX package

SDMX 2.1 information model

(c) 2014 Dr. Leo (fhaxbox66@gmail.com)
'''

from pandasdmx.utils import IsIterable
from IPython.config.loader import Config 
from IPython.utils.traitlets import (HasTraits, Unicode, Instance, List, Bool, 
            Any, This, Enum, Dict)



class InternationalString(Config):
    
    def __init__(self, *args, **kwargs):
        super(InternationalString, self).__init__(*args, **kwargs)
    
    def get_locales(self): return self.keys()
    
    def get_labels(self): return self.values()
    
        
class Annotation(HasTraits):
    identity = Unicode()
    title = Unicode()
    atype = Unicode()
    url = Unicode()
    text = Instance(InternationalString)
        
    def __init__(self, *args, identity= u'', title= u'', atype= u'', url= u'', text =None, **kwargs):
        super(Annotation, self).__init__(*args, **kwargs)
        self.identity, self.title, self.atype, self.url, self.text = (identity, title,
                                                               atype, url, text)
        
    def __str__(self):
        return 'Annotation: title=%s' , self.title  

class AnnotableArtefact(HasTraits):
    annotations = List()
    
    def __init__(self, *args, **kwargs):
        super(AnnotableArtefact, self).__init__(*args, **kwargs)
        for a in args:
            if isinstance(a, Annotation): self.annotations.append(a)
            else: raise TypeError(
                "Positional arguments must be of type 'Annotation'. %s given.", 
                type(a))
        
class IdentifiableArtefact(AnnotableArtefact):
    identity = Unicode()
    urn = Unicode
    uri = Unicode
    
    def __init__(self, *args, identity = u'', urn = u'', uri = u'', **kwargs):
        super(IdentifiableArtefact, self).__init__(*args, **kwargs)
        self.identity = identity
        self.urn = urn
        self.uri = uri
        
class NameableArtefact(IdentifiableArtefact):
    name = Instance(InternationalString)
    description = Instance(InternationalString)
    
    def __init__(self, *args, name=None, 
                 description =None, **kwargs):
        super(NameableArtefact, self).__init__(*args, **kwargs)
        self.name = name
        self.description = description
        
class VersionableArtefact(NameableArtefact):
    version = Unicode
    valid_from = Unicode
    valid_to = Unicode
    
    def __init__(self, *args, version = u'', valid_from = u'', valid_to = u'', **kwargs):
        super(VersionableArtefact, self).__init__(*args, **kwargs)
        self.version = version
        self.valid_from = valid_from
        self.valid_to = valid_to        

class MaintainableArtefact(VersionableArtefact):
    final = Bool
    is_external_ref = Bool
    structure_url = Unicode
    service_url = Unicode
    maintainer = Unicode() # Should be a reference?
    def __init__(self, *args, final = True, is_external_ref = False,
                 structure_url = u'', service_url = u'', maintainer = u'', **kwargs):
        super(MaintainableArtefact, self).__init__(*args, **kwargs)
        self.final = final
        self.is_external_ref = is_external_ref               
        self.structure_url = structure_url
        self.service_url = service_url
        self.maintainer = maintainer 
    
    
class ItemScheme(MaintainableArtefact, IsIterable):
    is_partial = Bool
            
    def __init__(self, *args, is_partial = False, **kwargs):
        super(ItemScheme, self).__init__(*args, **kwargs)
        self.is_partial = is_partial

        
class Item(NameableArtefact, IsIterable):
    parent = This # should include subclasses of Item
    children = List 
    
    def __init__(self, *args, parent = None, children = [], **kwargs):
        super(Item, self).__init__(*args, **kwargs)
        self.parent = parent
        self.children = children
         
class Structure(MaintainableArtefact):
    # the groupings are added in subclasses as class attributes. 
    # This deviates from the info model
    pass

class StructureUsage(MaintainableArtefact):
    structure = Instance(Structure)
    
    def __init__(self, structure, *args, **kwargs):
        super(StructureUsage, self).__init__(*args, **kwargs)
        self.structure = structure
    
    
class Componentlist(IdentifiableArtefact, IsIterable): pass
# Components are passed through the items attribute required by the IsIterable superclass.
# The 'components' attribute foreseen in the model is thus omitted. 


class Representation(HasTraits):
    enumerated = Instance(ItemScheme)
    not_enumerated = List # of facets
    def __init__(self, *args, enumerated =None, not_enumerated = [], **kwargs):
        super(Representation, self).__init__(*args, **kwargs)
        self.enumerated = enumerated
        self.not_enumerated = not_enumerated
        
        
class Facet(HasTraits):
    facet_type = Dict # for attributes such as isSequence, interval 
    facet_value_type = Enum('String', 'Big Integer', 'Integer', 'Long',
                            'Short', 'Double', 'Boolean', 'URI', 'DateTime', 
                'Time', 'GregorianYear', 'GregorianMonth', 'GregorianDate', 
                'Day', 'MonthDay', 'Duration')
    itemscheme_facet = Unicode # to be completed
    
    def __init__(self, *args, facet_type = None, facet_value_type = u'', 
                 itemscheme_facet = u'', **kwargs):
        super(Facet, self).__init__(*args, **kwargs)
        self.facet_type = facet_type
        self.facet_value_type = facet_value_type
        self.itemscheme_facet = itemschemefacet
               
        

class Component(IdentifiableArtefact):
    concept_id = Instance(Concept)
    local_repr = Instance(Representation)

    def __init__(self, *args, concept_id =None, local_repr =None, **kwargs):
        super(Component, self).__init__(*args, **kwargs)
        self.concept_id = concept_id
        self.local_repr = local_repr

class Codelist(ItemScheme): pass
class Code(Item): pass


class ConceptScheme(ItemScheme): pass


class IsoConceptReference: pass # to be completed


class Concept(Item):
    core_repr = Instance(Representation)
    iso_concept = Instance(IsoConceptReference) 
    
    def __init__(self, *args, core_repr =None, iso_concept =None, **kwargs):
        super(Concept, self).__init__(*args, **kwargs)
        self.core_repr = core_repr
        self.iso_concept = iso_concept
        
        



class CategoryScheme(ItemScheme): pass

class Category(Item): pass

class Categorization(MaintainableArtefact):
    artefact = Instance(IdentifiableArtefact)
    categorized_by = Instance(Category)
    
    def __init__(self, id_artefact, category, *args, **kwargs):
        super(Categorization, self).__init__(*args, **kwargs)
        self.artefact = id_artefact
        self.categorized_by = category
        
class IdentifiableObjectType: pass
class ConstraintRoleType: pass    

class DataSet: pass 

    
class StructureSpecificDataSet: pass
 
class GenericDataSet: pass

class GenericTimeSeriesDataSet: pass 
 
class StructureSpecificTimeSeriesDataSet: pass


class Key: pass
class SeriesKey: pass
class GroupKey: pass

class DataflowDefinition(MaintainableArtefact, StructureUsage): pass 
    # really inherit from maintainableartefact? 

    
    

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
    


class DataAttribute(Component):
    # relationship may be None, dataset, list of dimensions, group or primary measure
    # We represent this as Enum rather than superclasses as in the model. to be reconsidered.
    relationship = Enum('None', 'dataset', 'dimensions', 'group', 'primaryMeasure')  
    role = Instance(Concept)
    usage_status = Enum('mandatory', 'conditional') # generalise this through constraint?
    
    def __init__(self, *args, role =None, relationship = 'None', **kwargs):
        super(DataAttribute, self).__init__(*args, **kwargs)
        self.relationship = relationship
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
    
    