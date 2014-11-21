# encoding: utf-8

import pandas as PD
import numpy as NP
import lxml.etree
from IPython.utils.traitlets import Unicode
from IPython.config.configurable import Configurable
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



class Resource(Configurable):
    
    def __init__(self, agency_id, client, **kwargs):
        super(Resource, self).__init__()
        self.client = client
        self.agency_id = agency_id
    
    def get(self, *args, **kwargs):
        # Construct the URL and get source file
        url = self.make_url(*args, **kwargs)
        source = self.client.get(url)
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
        
    

    def make_url(self, flowref, *args, key = '', startperiod = None, endperiod = None, **kwargs):
        parts = [self.resource_name, flowref]
        if key: parts.append(key)
        query_url = '/'.join(parts)
        if startperiod: query_url += '?startperiod={0}'.format(startperiod)
        if endperiod: query_url += '&endperiod={0}'.format(endperiod) 
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
            


class Data20(Resource):
    """
    Data parser for SDMX 2.0
    """
    
    def url(self, *args):
        """
        generate URL for REST query
        """
        flowref, key = args
        resource = 'GenericData'
        key__ = ''
        for key_, value_ in key.items():
            key__ += '&' + key_ + '=' + value_
        key = key__
        
        if startperiod and endperiod:
            query = (resource + '?dataflow=' + flowRef + key
            + 'startperiod=' + startperiod
            + '&endPeriod=' + endperiod)
        else:
            query = resource + '?dataflow=' + flowRef + key
        return '/'.join([self.sdmx_url,query])


    def parse(self, source):
        CodeTuple = None
        parser = lxml.etree.XMLParser(
            ns_clean=True, recover=True)
        tree = lxml.etree.fromstring(source, parser = parser)
        for series in tree.iterfind(".//generic:Series",
                                 namespaces=tree.nsmap):
            raw_dates, raw_values, raw_status = [], [], []
            code_keys, code_values = [], []
            for codes_ in series.iterfind(".//generic:SeriesKey",
                                       namespaces=tree.nsmap):
                for key in codes_.iterfind(".//generic:Value",
                                           namespaces=tree.nsmap):
                    
                    if not CodeTuple: code_keys.append(key.get('concept')) 
                    code_values.append(key.get('value'))
            if not CodeTuple:
                CodeTuple = make_namedtuple(code_keys) 
            codes = CodeTuple._make(code_values)
                           
            for observation in series.iterfind(".//generic:Obs",
                                               namespaces=tree.nsmap):
                dimensions = observation.xpath(".//generic:Time",
                                               namespaces=tree.nsmap)
                values = observation.xpath(".//generic:ObsValue",
                                           namespaces=tree.nsmap)
                value = values[0].get('value')
                observation_status = 'A'
                for attribute in \
                    observation.iterfind(".//generic:Attributes",
                                         namespaces=tree.nsmap):
                    for observation_status_ in \
                        attribute.xpath(
                            ".//generic:Value[@concept='OBS_STATUS']",
                            namespaces=tree.nsmap):
                        if observation_status_:
                            observation_status \
                                = observation_status_.get('value')
                                
                raw_dates.append(dimensions)
                raw_values.append(value)
                raw_status.append(observation_status)
            yield codes, raw_dates, raw_values, raw_status
        
        
class Dataflow21(Resource):
    language = Unicode('en', config = True)
    
    def __init__(self, *args, **kwargs):
        super(Dataflow21, self).__init__(*args, **kwargs)
        
            
    def make_url(self):
        return '/'.join(['dataflow', self.agency_id, 'all', 'latest'])        
        
            
    def parse(self, source):        
            
        tree = lxml.etree.parse(source).getroot() 
         
        dataflow_path = ".//str:Dataflow"
        name_path = ".//com:Name"
        for dataflow in tree.iterfind(dataflow_path,
                                               namespaces=tree.nsmap):
            flowref = dataflow.get('id')
            agencyID = dataflow.get('agencyID')
            version = dataflow.get('version')
            for title in dataflow.iterfind(name_path,
                namespaces=tree.nsmap):
                descr_lang = title.values()[0]
                if descr_lang == self.language: 
                    row = ('"' + agencyID + '"', '"' + flowref + '"', 
                               version, '"' + title.text + '"')
            yield row
                        
    def transform(self, *args):
        return args                        
                                   
class Dataflow20(Resource):
                        
    def parse(self, source):        
            url = '/'.join([self.sdmx_url, 'Dataflow'])
            tree = self.get_source(url, to_file = to_file, from_file = from_file)
            # Init the database and store the parsed data in it 
            if to_database:
                self._init_database(table)
                            
                cur = self.db.cursor()
                dataflow_path = ".//structure:Dataflow"
                name_path = ".//structure:Name"
                keyid_path = ".//structure:KeyFamilyID"
                for dataflow in tree.iterfind(dataflow_path,
                                                   namespaces=tree.nsmap):
                    flowref = dataflow.find(keyid_path,
                                                   namespaces=tree.nsmap).text
               
                    agencyID = dataflow.get('agencyID')
                    version = dataflow.get('version')
                    title_text = dataflow.find(name_path,
                                                   namespaces=tree.nsmap).text

                    row = ('"' + agencyID + '"', '"' + flowref + '"', 
                                   version, '"' + title_text + '"')
                    cur.execute(u'''INSERT INTO {0} VALUES 
                            (NULL, {1[0]}, {1[1]}, {1[2]}, {1[3]})'''.format(
                            table, row))
                   
                           
        

                        
class Codes:
    def get_codes(self, flowRef, to_file = None, from_file = None):
        """Data definitions

        Returns a dictionnary describing the available dimensions for a specific flowRef.

        :param flowRef: Identifier of the dataflow
        :type flowRef: str or sqlite3.Row
        :return: OrderedDict
        """
        
        if isinstance(flowRef, sqlite3.Row):
            flowRef = flowRef['flowref']
        if self.version == '2_1':
            url = '/'.join([self.sdmx_url, 'datastructure', self.agencyID,
                            self.agencyID + '_' + flowRef])
            tree = self.get_source(url, to_file = to_file, from_file = from_file)
            codelists_path = ".//str:Codelists"
            codelist_path = ".//str:Codelist"
            name_path = ".//com:Name"
            code_path = ".//str:Code"
            _codes = OrderedDict()
            codelists = tree.xpath(codelists_path,
                                          namespaces=tree.nsmap)
            for codelists_ in codelists:
                for codelist in codelists_.iterfind(codelist_path,
                                                    namespaces=tree.nsmap):
                    name = codelist.xpath(name_path, namespaces=tree.nsmap)
                    name = name[0]
                    name = name.text
                    # a dot "." can't be part of a JSON field name
                    name = re.sub(r"\.","",name)
                    code = {}
                    for code_ in codelist.iterfind(code_path,
                                                   namespaces=tree.nsmap):
                        code_key = code_.get('id')
                        code_name = code_.xpath(name_path,
                                                namespaces=tree.nsmap)
                        code_name = code_name[0]
                        code[code_key] = code_name.text
                    _codes[name] = code
        if self.version == '2_0':
            codelists_path = ".//message:CodeLists"
            codelist_path = ".//structure:CodeList"
            code_path = ".//structure:Code"
            description_path = ".//structure:Description"
            url = '/'.join([self.sdmx_url, 'KeyFamily', flowRef])
            tree = self.get_source(url)
            _codes = OrderedDict()
            codelists = tree.xpath(codelists_path,
                                          namespaces=tree.nsmap)
            for codelists_ in codelists:
                for codelist in codelists_.iterfind(codelist_path,
                                                    namespaces=tree.nsmap):
                    name = codelist.get('id')
                    name = name[3:]
                    # a dot "." can't be part of a JSON field name
                    name = re.sub(r"\.","",name)
                    code = {}
                    for code_ in codelist.iterfind(code_path,
                                                   namespaces=tree.nsmap):
                        code_key = code_.get('value')
                        code_name = code_.xpath(description_path,
                                                namespaces=tree.nsmap)
                        code_name = code_name[0]
                        code[code_key] = code_name.text
                    _codes[name] = code
        return _codes

class constraints:
    
    def get_constraints(self, flowref):
        """
        return content constraints i.e. codes available
        for a given dataflow.
        to be completed.
        """
        
        url = '/'.join([self.sdmx_url, 'contentconstraint', self.agencyID, flowRef + '_CONSTRAINTS'])
        
