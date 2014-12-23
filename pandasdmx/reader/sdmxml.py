# encoding: utf-8

from lxml import objectify
from IPython.utils.traitlets import Unicode
from pandasdmx import model
from .common import Reader


      
class SDMXMLReader(Reader):
    
    """
    Read SDMX-ML 2.1 and expose it as instances from pandasdmx.model
    """
    
    def parse(self, source):
        return objectify.parse(self.source).getroot() 
        
        
        
    

 
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
    
    
        