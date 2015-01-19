# encoding: utf-8


from pandasdmx.utils import DictLike
from pandasdmx import model
from .common import Reader
from lxml import objectify



 
class SDMXMLReader(Reader):

    
    """
    Read SDMX-ML 2.1 and expose it as instances from pandasdmx.model
    """
    

    def initialize(self, source):
        root = objectify.parse(source).getroot()
        self.response = model.Response(self, root)
        return self.response 
    
        
    def dispatch(self, elem):
        model_class = self.model_map.get(elem.tag)
        if model_class: return model_class(self, elem)
        else: return elem   
         
        
        
    def mes_header(self, elem):
        'return a message header. elem must be the document root.'
        return model.Header(self, elem.xpath('mes:Header', namespaces = elem.nsmap)[0])
    
    def header_id(self, elem):
        return elem.ID[0].text 

    def annotations(self, elem):
        return self._structures(elem, 'com:Annotations/com:Annotation', 
                                model.Annotation)
                
                
    def identity(self, elem):
        return elem.get('id')
    
    def urn(self, elem):
        return elem.get('urn')

    def uri(self, elem):
        return elem.get('uri')
        
        
    def agencyID(self, elem):
        return elem.get('agencyID')
    
    
    def _international_string(self, elem, tagname):
        languages = elem.xpath('com:{0}/@xml:lang'.format(tagname), 
                               namespaces = elem.nsmap)
        strings = elem.xpath('com:{0}/text()'.format(tagname), 
                             namespaces = elem.nsmap)
        return DictLike(zip(languages, strings))

    def description(self, elem):
        return self._international_string(elem, 'Description') 
        
    def name(self, elem):
        return self._international_string(elem, 'Name') 
        

    def header_prepared(self, elem):
        return elem.Prepared[0].text # convert this to datetime obj?
        
    def header_sender(self, elem):
        return DictLike(elem.Sender.attrib)

    def header_error(self, elem):
        try:
            return DictLike(elem.Error.attrib)
        except AttributeError: return None
                     
    def _items(self, elem, path, model_cls):
        '''
        return dict mapping IDs to item instances from model.
        elem must be an item scheme
        '''    
        return {e.get('id') : model_cls(self, e) for e in elem.xpath(path, 
                    namespaces = elem.nsmap)} 
                     
    def _structures(self, elem, path, model_cls):
    
        '''
        Helper method called by codelists() etc.
        return DictLike mapping structure IDs to model claas for the structure
        '''
        return DictLike({e.get('id') : model_cls(self, e) for e in  
                    elem.xpath(path, namespaces = elem.nsmap)})
        
    def codelists(self, elem):
        return self._structures(elem, 'mes:Structures/str:Codelists/str:Codelist', 
                                model.Codelist)
    
    
    def codes(self, elem):
        return self._items(elem, 'str:Code', model.Code)

    
    def conceptschemes(self, elem):
        return self._structures(elem, 'mes:Structures/str:Concepts/str:ConceptScheme', model.ConceptScheme)
        
        
    def concepts(self, elem):
        return self._items(elem, 'str:Concept', model.Concept)

        
    def isfinal(self, elem):
        return bool(elem.get('isFinal')) 
        
    def dataflows(self, elem):
        return self._structures(elem, 'mes:Structures/str:Dataflows/str:Dataflow', 
                                model.DataflowDefinition)
    
    def structure(self, elem):
        '''
        return content of a model.Structure.  
        '''
        return model.Structure(self, elem.xpath('str:Structure', 
                                                namespaces = elem.nsmap))
     
    def datastructures(self, elem):
        return self._structures(elem, 'mes:Structures/str:DataStructures/str:DataStructure', 
                                model.DataStructureDefinition)
    
    def dimdescriptor(self, elem):
        nodes = elem.xpath('str:DataStructureComponents/str:DimensionList',
                          namespaces = elem.nsmap) 
        return model.DimensionDescriptor(self, nodes[0])
    
    def dimension_items(self, elem):
        d = self._structures(elem, 'str:Dimension', model.Dimension)
        d.update(self._structures(elem, 'str:TimeDimension', model.TimeDimension))
        d.update(self._structures(elem, 'str:MeasureDimension', model.MeasureDimension))
        return d
         
    def concept_id(self, elem):
        # called by model.Component.concept
        c_id = elem.xpath('str:ConceptIdentity/Ref/@id', 
                          namespaces = elem.nsmap)[0]
        parent_id = elem.xpath('str:ConceptIdentity/Ref/@maintainableParentID',
                               namespaces = elem.nsmap)[0]
        return self.response.conceptschemes[parent_id][c_id]
        
    def position(self, elem):
        # called by model.Dimension
        return int(elem.get('position')) 
    
    def localrepr(self, elem):
        node = elem.xpath('str:LocalRepresentation',
                          namespaces = elem.nsmap)[0]
        enum = node.xpath('str:Enumeration/Ref/@id',
                          namespaces = node.nsmap)
        if enum: enum = self.response.codelists[enum[0]]
        else: enum = None
        return model.Representation(self, node, enum = enum)
         
        
    def attributes(self, elem):
        nodes = elem.xpath('str:DataStructureComponents/str:AttributeList',
                          namespaces = elem.nsmap) 
        return model.AttributeDescriptor(self, nodes[0])

    def attribute_items(self, elem):
        return self._structures(elem, 'str:Attribute', model.DataAttribute)
    
    def assignment_status(self, elem):
        return elem.xpath('@assignmentStatus')[0]
        
        
    def measures(self, elem):
        nodes = elem.xpath('str:DataStructureComponents/str:MeasureList',
                          namespaces = elem.nsmap) 
        return model.MeasureDescriptor(self, nodes[0])

    def measure_items(self, elem):
        return self._structures(elem, 'str:PrimaryMeasure', model.PrimaryMeasure)
    


 
    def parse_series(self, source):
        """
        generator to parse data from xml. Iterate over series
        """
        CodeTuple = None
        generic_ns = '{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}'
        series_tag = generic_ns + 'Series'
        serieskey_tag = series_tag + 'Key'
        value_tag = generic_ns + 'Value'
        obs_tag = generic_ns + 'Obs'
        obsdim_tag = generic_ns + 'ObsDimension'
        obsvalue_tag = generic_ns + 'ObsValue'
        attributes_tag = generic_ns + 'Attributes' 
        context = lxml.etree.iterparse(source, tag = series_tag)
        
        for _, series in context: 
            raw_dates, raw_values, raw_status = [], [], []
            
            for elem in series.iterchildren():
                if elem.tag == serieskey_tag:
                    code_keys, code_values = [], []
                    for value in elem.iter(value_tag):
                        if not CodeTuple: code_keys.append(value.get('id')) 
                        code_values.append(value.get('value'))
                elif elem.tag == obs_tag:
                    for elem1 in elem.iterchildren():
                        observation_status = 'A'
                        if elem1.tag == obsdim_tag:
                            dimension = elem1.get('value')
                            # Prepare time spans such as Q1 or S2 to make it parsable
                            suffix = dimension[-2:]
                            if suffix in time_spans:
                                dimension = dimension[:-2] + time_spans[suffix]
                            raw_dates.append(dimension) 
                        elif elem1.tag == obsvalue_tag:
                            value = elem1.get('value')
                            raw_values.append(value)
                        elif elem1.tag == attributes_tag:
                            for elem2 in elem1.iter(".//"+generic_ns+"Value[@id='OBS_STATUS']"):
                                observation_status = elem2.get('value')
                            raw_status.append(observation_status)
            if not CodeTuple:
                CodeTuple = make_namedtuple(code_keys) 
            codes = CodeTuple._make(code_values)
            series.clear()
            yield codes, raw_dates, raw_values, raw_status 
    
    