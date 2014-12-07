# encoding: utf-8

import pandas as PD
import numpy as NP
import lxml.etree
from IPython.utils.traitlets import Unicode
from IPython.config.configurable import Configurable, LoggingConfigurable
from collections import OrderedDict, namedtuple


# Time span conversions not recognised by pandas:

time_spans = {
    'Q1' : '01-01',
    'Q2' : '04-01',
    'Q3' : '07-01',
    'Q4' : '10-01',
    'S1' : '01-01',
    'S2' : '07-01'
}    


# Allow convenient checking for existing namedtuple classes that can be reused for column metadata  
tuple_classes = {}

def make_namedtuple(fields):
    """
    Wrap namedtuple function from the collections stdlib module
    to return a singleton if a nametuple with the same field names
    has already been created. 
        
    return a subclass of tuple instance as does namedtuple
    """
    fields = tuple(fields)
    if not fields in tuple_classes: 
        tuple_classes[fields] = namedtuple(
            'SDMXMetadata', fields)
    return tuple_classes[fields]



class Resource(LoggingConfigurable):
    
    def __init__(self, agency_id, client, **kwargs):
        super(Resource, self).__init__()
        self.client = client
        self.agency_id = agency_id
    
    def get(self, *args, from_file = None, to_file = None, **kwargs):
        # Construct the URL and get source file
        url_suffix = self.make_url(*args, **kwargs)
        source = self.client.get(url_suffix, from_file = from_file)
        if to_file:
            with open(to_file, 'wb') as dest:
                dest.write(source.read())
                source.seek(0)

        return self.render(source)
    

    def make_url(self): pass
    
    def parse(self): raise NotImplemented
    
    def render(self, source, **kwargs):
        result_list = [self.transform(*l, **kwargs) for l in self.parse(source)]
        
        if 'merge' in kwargs and kwargs['merge']: 
            return self.combine(result_list, **kwargs)
        else: return result_list

    
    def combine(self, result_list, **kwargs): 
        return result_list 
    
                
class Data21(Resource):
    resource_name = 'data'
    """
    Data resource in SDMX v2.1
    """
    
    def __init__(self, *args, **kwargs):
        super(Data21, self).__init__(*args, **kwargs)
        # dtype for Series. Future versions should support other dtypes 
        # such as int or categorical.
        self.datatype = NP.float64
        
    

    def make_url(self, flowref, key = '', startperiod = None, endperiod = None):
        parts = [self.resource_name, flowref]
        if key: parts.append(key)
        query_url = '/'.join(parts)
        if startperiod: 
            query_url += '?startperiod={0}'.format(startperiod)
            if endperiod: query_url += '&endperiod={0}'.format(endperiod)
        elif endperiod: query_url += '?endperiod={0}'.format(endperiod) 
        return query_url
    
 
    def parse(self, source):
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
    
    
    def transform(self, *args, **kwargs):
        """
        Transform the 5-tuple returned by self.parse into PD.Series
        """ 
        codes, raw_dates, raw_values, raw_status = args 
        if 'FREQ' in codes._fields:
            if codes.FREQ == 'A':
                freq_str = 'Y'
            else: 
                freq_str = codes.FREQ
            dates = PD.PeriodIndex(raw_dates, freq = freq_str)
        else:
            dates = PD.to_datetime(raw_dates)
        value_series = PD.TimeSeries(raw_values, index = dates, 
                    dtype = self.datatype, name = codes)
        return value_series

    
    def combine(self, series_list, **args):
        # Generate DataFrame    
            
        # Use the codes to generate the MultiIndex levels
        code_sets = {k : set([getattr(s.name, k) for s in series_list]) 
                     for k in series_list[0].name._fields}
            
        global_codes = {k : code_sets[k].pop() for k in code_sets 
                            if len(code_sets[k]) == 1}
        # Remove global codes as they should not lead to index levels in the DataFrame 
        for k in global_codes: code_sets.pop(k)
                
        # Sort the keys with llargest set first  
        lengths = [(len(code_sets[k]), k) for k in code_sets]
        lengths.sort(reverse = True)
        sorted_keys = [k[1] for k in lengths]        
        # Construct the multi-index from the Series.name tuples
        raw_index = [tuple([getattr(s.name, k) for k in sorted_keys]) 
                      for s in series_list]  
        column_index = PD.MultiIndex.from_tuples(raw_index, names = sorted_keys)
        df = PD.DataFrame(columns = column_index, index = series_list[0].index)
        # Add the series to the DataFrame
        for pos, s in zip(raw_index, series_list): df[pos] = s       
        
        #  Attach global metadata
        # df.meta = global_codes 
        return df
            
        
class CodeList21(Resource):
    language = Unicode('en', config = True)
    
    def __init__(self, *args, **kwargs):
        super(CodeList21, self).__init__(*args, **kwargs)
        
            
    def make_url(self):
        return '/'.join(['dataflow', self.agency_id, 'all', 'latest'])        
        
            
    def parse(self, source):        
            
        tree = lxml.etree.parse(source).getroot() 
         
        dataflow_path = ".//str:Dataflow"
        name_path = ".//com:Name"
        for dataflow in tree.iterfind(dataflow_path,
                                               namespaces=tree.nsmap):
            flowref = dataflow.get('id')[1:-2]
            agencyID = dataflow.get('agencyID')
            version = dataflow.get('version')
            row = None
            for title in dataflow.iterfind(name_path,
                namespaces=tree.nsmap):
                descr_lang = title.values()[0]
                if descr_lang == self.language: 
                    row = (agencyID, flowref, 
                               version, title.text)
                    break
            if row: yield row
            else: raise ValueError('No description for dataflow_id {0} and language {1}.'.format(
                                            flowref, self.language))
                        
    def transform(self, *args):
        return args                        



class Structure21(CodeList21):
    
    def __init__(self, *args, **kwargs):
        super(Structure21, self).__init__(*args, **kwargs)

        
        
    def make_url(self, flowref):
        return '/'.join(['datastructure', self.agency_id, 'DSD_' + flowref])
        
    def render(self, source, language = None):
        if not language: language = self.language
        return self.parse(source, language)       
        
    def parse(self, source, language):
        parser = lxml.etree.XMLParser(ns_clean=True)
        tree = lxml.etree.parse(source, parser).getroot()
        
        # nsmap = {k : v for k,v in tree.nsmap.items() if k}
        nsmap = tree.nsmap
       
        dimensions = OrderedDict()
        
        for dimensions_list_ in  tree.iterfind("{*}CodeLists",namespaces=nsmap):
            print('hello')
            for dimensions_list in dimensions_list_.iterfind(".//structure:CodeList",
                                                namespaces=nsmap):
                name = dimensions_list.get('id')
                # truncate intial "CL_" in name
                name = name[3:]
                print(name)
                dimension = []
                for dimension_ in dimensions_list.iterfind(".//structure:Code",
                                               namespaces=nsmap):
                    dimension_key = dimension_.get("value")
                    for desc in dimension_:
                        if desc.attrib.items()[0][1] == language:
                            dimension.append([dimension_key, desc.text])
                            break
                dimensions[name] = dimension
        return dimensions

class Categories(Resource):
    def __init__(self, *args, **kwargs):
        super(Categories, self).__init__(*args, **kwargs)
    
    def make_url(self):
        return 'categoryscheme'
    
    def render(self, source):
        return source
    