        #! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. module:: pysdmx
    :platform: Unix, Windows
    :synopsis: Python interface for SDMX

.. :moduleauthor :: Widukind team <widukind-dev@cepremap.org>
"""

import requests
import pandas as PD
import numpy as NP
import lxml.etree
import sqlite3
from io import BytesIO
import re, zipfile
from collections import OrderedDict, namedtuple


__all__ = ['eurostat', 'ecb', 'fao', 'ilo']


# Allow easy checking for existing namedtuple classes that can be reused for column metadata  
tuple_classes = []

def to_namedtuple(mapping):
    """
    Convert a list of (key,value) tuples into a namedtuple. If there is not already 
    a suitable class in 'tuple_classes', Create a new class first and append it to the list.
        
    return a namedtuple instance
    """
    # convert to OrderedDict
    codes = OrderedDict()
    for k,v in mapping: 
        codes[k] = v
    # Check if there is already a suitable class
    for t in tuple_classes:
        try:
            code_tuple = t(**codes)
            break
        except TypeError:
            if t is tuple_classes[-1]: 
                tuple_classes.append(namedtuple(
                'CodeTuple' + str(len(tuple_classes)), codes.keys()))
                code_tuple = tuple_classes[-1](**codes)
    else:
        tuple_classes.append(namedtuple(
            'CodeTuple' + str(len(tuple_classes)), codes.keys()))
        code_tuple = tuple_classes[0](**codes)
    return code_tuple
            
        
               
class SDMX_REST(object):
    """Data provider. This is the main class that allows practical access to all the data.

    :ivar sdmx_url: The URL of the SDMX endpoint, the webservice employed to access the data.
    :type sdmx_url: str
    :ivar agencyID: An identifier of the statistical provider.
    :type agencyID: str
    """
    def __init__(self, sdmx_url, version, agencyID):
        self.sdmx_url = sdmx_url
        self.agencyID = agencyID
        self.version = version

    
    def get_tree(self, url, to_file = None, from_file = None):
        '''
        Read xml data from URL or local file.
        Store the fetched string in a local file if specified to save download time next time.
        Return lxml ElementTree instance after parsing
        Raise error if file could not be obtained.
 '''
        if from_file:
            # Load data from local file 
            with open(from_file, 'rb') as f:
                xml_str = f.read()
        else:
            xml_str = self.request(url)
        parser = lxml.etree.XMLParser(
            ns_clean=True, recover=True, encoding='utf-8')
        tree = lxml.etree.fromstring(xml_str, parser = parser)
        if to_file:
            with open(to_file, 'wb') as f:
                f.write(xml_str)
        return tree
         
    
    def request(self, url):
        """
        Retrieve SDMX messages.
        If needed, override in subclasses to support other data providers.

        :param url: The URL of the message.
        :type url: str
        :return: the xml data as string
        """
        
        request = requests.get(url, timeout= 20)
        if request.status_code == requests.codes.ok:
            xml_str = request.text.encode('utf-8')
        elif request.status_code == 430:
            #Sometimes, eurostat creates a zipfile when the query is too large. We have to wait for the file to be generated.
            parser = lxml.etree.XMLParser(
                                          ns_clean=True, recover=True, encoding='utf-8')
            tree = lxml.etree.fromstring(xml_str, parser = parser)
            messages = tree.xpath('.//footer:Message/common:Text',
                                      namespaces = tree.nsmap)
            regex_ = re.compile("Due to the large query the response will be written "
                                "to a file which will be located under URL: (.*)")
            matches = [regex_.match(element.text) for element in messages]
            if matches:
                xml_str = None
                i = 30
                while i<101:
                    time.sleep(i)
                    i = i+10
                    url = matches[0].groups()[0]
                    request = requests.get(url)
                    if request.headers['content-type'] == "application/octet-stream":
                        buffer = BytesIO(request.content)
                        file = zipfile.ZipFile(buffer)
                        filename = file.namelist()[0]
                        xml_str = file.read(filename)
                        break
                        if xml_str is None:
                            raise Exception("The web server didn't provide the file you are looking for.")
            else:
                raise ValueError("Error getting client({})".format(request.status_code))      
        else:
            raise ValueError("Error getting client({})".format(request.status_code))      
        return xml_str
    
    
    def _init_database(self, filename, tablename):
        '''
        Helper method to initialize database.
        Called by dataflows()
        Return: sqlite3.Connection
        '''
        conn = sqlite3.connect(filename)
        conn.row_factory = sqlite3.Row
        # Check if table already exists
        contents = conn.execute('select * from SQLITE_MASTER')
        exists = [row for row in contents
            if row['type'] == 'table' and row['name'] == tablename]
        if not exists:
            conn.execute(u'''create table {0} 
                (id primary key, agency, version, title)'''.format( 
                tablename))
        return conn

    def dataflows(self, language = 'en', to_file = ':memory:', from_file = None,
                  table = None):
        """
        Get list of available dataflows 
        Arguments:
        :param: language: keyword argument specifying the language of the 
        dataflow titles to be stored. This feature is not supported by 
        SDMX v2.0.  
        Used only when sqlite3 is used to store
        the data. See the semantics of the 'to_file' argument.
        Defaults to 'en' for English.
        :type: str
        :param: to_file: keyword argument specifying the filename of a file 
        to write the dataflows list to. If it ends with '.xml',
        the requested xml file is stored locally and None is returned. 
        Otherwise an sqlite database is created and the dataflows are inserted 
        into a table whose name is specified by the 'table' argument.
        If that table does not yet exist, it is first created.
        (defaults to ':memory:' for an in memory sqlite database.
        :type: str
        :param: 'from_file': Read the xml data from an xml file rather than 
        requesting the xml data via http from the data provider. 
        By convention, 'from_file' should have the 
        extension '.xml' as such file can conveniently be written by passing
        a filename through the 'to_file' keyword argument.    
        Use 'sqlite3.connect()' to connect to an existing database containing dataflows.
        :param: table: name of the table into which the dataflow descriptions will be inserted.
        If the database does not contain a table of this name, it is first created.
        Defaults to self.agencyID
        :type: str 
     
        return: sqlite3.Connection or None (if data is written to '.xml' file
        """
        
        # Write to local xml file if file extension is '.xml'. 
        # Otherwise write the dataflows to an existing or newly created 
        # sqlite database with the specified filename.
        if to_file.endswith('.xml'):
            to_file_arg = to_file # will be passed to get_tree() 
        else:
            to_file_arg = None # do not store the xml file as we use sqlite
            if not table: table = self.agencyID # set to default 
            
        if self.version == '2_1':
            url = '/'.join([self.sdmx_url, 'dataflow', self.agencyID, 'all', 'latest'])
            tree = self.get_tree(url, to_file = to_file_arg, from_file = from_file)
            if to_file_arg:
                # local .xml file has already been stored. So do nothing.
                return None
            else: 
                # Init the database and store 
                # the parsed data in it
                conn = self._init_database(to_file, table)
                cur = conn.cursor()
                dataflow_path = ".//str:Dataflow"
                name_path = ".//com:Name"
                for dataflow in tree.iterfind(dataflow_path,
                                                   namespaces=tree.nsmap):
                    id = dataflow.get('id')
                    agencyID = dataflow.get('agencyID')
                    version = dataflow.get('version')
                    for title in dataflow.iterfind(name_path,
                                                   namespaces=tree.nsmap):
                        descr_lang = title.values()[0]
                        if descr_lang == language: 
                            row = ('"' + id + '"', '"' + agencyID + '"', 
                                   version, '"""' + title.text + '"""')
                            cur.execute(u'''INSERT INTO {0} VALUES 
                            ({1[0]}, {1[1]}, {1[2]}, {1[3]})'''.format(
                                           self.agencyID, row))
                    
        elif self.version == '2_0':
            url = '/'.join([self.sdmx_url, 'Dataflow'])
            tree = self.get_tree(url, to_file = to_file_arg, from_file = from_file)
            if to_file_arg:
                # local .xml file has already been stored. So do nothing.
                return None
            else: 
                # Init the database and store 
                # the parsed data in it
                conn = self._init_database(to_file, table)
                cur = conn.cursor()
                dataflow_path = ".//structure:Dataflow"
                name_path = ".//structure:Name"
                keyid_path = ".//structure:KeyFamilyID"
                for dataflow in tree.iterfind(dataflow_path,
                                                   namespaces=tree.nsmap):
                    for id in dataflow.iterfind(keyid_path,
                                                   namespaces=tree.nsmap):
                        key = id.text
                    agencyID = dataflow.get('agencyID')
                    version = dataflow.get('version')
                    for title in dataflow.iterfind(name_path,
                                                   namespaces=tree.nsmap):
                        row = ('"' + key + '"', '"' + agencyID + '"', 
                                   version, '"""' + title.text + '"""')
                        cur.execute(u'''INSERT INTO {0} VALUES 
                            ({1[0]}, {1[1]}, {1[2]}, {1[3]})'''.format(
                            self.agencyID, row))

                        
        conn.commit()        
        return conn 

    def codes(self, flowRef, to_file = None, from_file = None):
        """Data definitions

        Returns a dictionnary describing the available dimensions for a specific flowRef.

        :param flowRef: Identifier of the dataflow
        :type flowRef: str or sqlite3.Row
        :return: dict"""
        if isinstance(flowRef, sqlite3.Row):
            flowRef = flowRef['id']
        if self.version == '2_1':
            url = '/'.join([self.sdmx_url, 'datastructure', self.agencyID, 'DSD_' + flowRef])
            tree = self.get_tree(url, to_file = to_file, from_file = from_file)
            codelists_path = ".//str:Codelists"
            codelist_path = ".//str:Codelist"
            name_path = ".//com:Name"
            code_path = ".//str:Code"
            self._codes = {}
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
                    code = OrderedDict()
                    for code_ in codelist.iterfind(code_path,
                                                   namespaces=tree.nsmap):
                        code_key = code_.get('id')
                        code_name = code_.xpath(name_path,
                                                namespaces=tree.nsmap)
                        code_name = code_name[0]
                        code[code_key] = code_name.text
                    self._codes[name] = code
        if self.version == '2_0':
            codelists_path = ".//message:CodeLists"
            codelist_path = ".//structure:CodeList"
            code_path = ".//structure:Code"
            description_path = ".//structure:Description"
            url = '/'.join([self.sdmx_url, 'KeyFamily', flowRef])
            tree = self.get_tree(url)
            self._codes = {}
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
                    self._codes[name] = code
        return self._codes


    def data(self, flowRef, key, startperiod=None, endperiod=None, 
        to_file = None, from_file = None, 
        concat = False):
        """Get data

        :param flowRef: an identifier of the data
        :type flowRef: str or sqlite3.Row from the table created 
        by the dataflows() method 
        :param key: a filter using codes (for example, .... for no filter ...BE for all the series related to Belgium) if using v2_1. In 2_0, you should be providing a dict following that syntax {dimension:value}
        :type key: str or dict
        :param startperiod: the starting date of the time series that will be downloaded (optional, default: None)
        :type startperiod: datetime.datetime()
        :param endperiod: the ending date of the time series that will be downloaded (optional, default: None)
        :type endperiod: datetime.datetime()
        :param to_file: if it is a string, the xml file is, after parsing it,
        written to a file with this name. Default: None
        :param from_file: if it is a string, the xml file is read from a file with that name instead of
        requesting the data via http. Default: None
        :concat: If False, return a tuple (l, d) where
        l is a list of the series whose name attributes contain 
        the metadata as namedtuple, and d is a dict containing any global metadata.
        If True: return a tuple (df, d) where df is a pandas.DataFrame
        with hierarchical index generated from the metadata. Explore the
        structure by issuing 'df.columns'.
        The order of index levels is determined by the number of actual values 
        found in the series' metadata for each key.
        If concat is a list of metadata keys, they determine the order of index levels.
        d: a dict of global metadata.    
        
        return tuple of the form (l, d) or (df, d)
        depending on the value of 'concat'.
        """
        if isinstance(flowRef, sqlite3.Row):
            flowRef = flowRef['id']
        series_list = []
        # dtype for Series. Future versions should support other dtypes 
        # such as int or categorical.
        datatype = NP.float64 
        
        if self.    version == '2_1':
            resource = 'data'
            if startperiod and endperiod:
                query = '/'.join([resource, flowRef, key
                        + '?startperiod=' + startperiod
                        + '&endPeriod=' + endperiod])
            else:
                query = '/'.join([resource, flowRef, key])
            url = '/'.join([self.sdmx_url,query])
            tree = self.get_tree(url, to_file = to_file, from_file = from_file)
            GENERIC = '{'+tree.nsmap['generic']+'}'
            
            for series in tree.iterfind(".//generic:Series",
                                             namespaces=tree.nsmap):
                raw_dates = []
                raw_values = []
                raw_status = []
                
                for elem in series.iterchildren():
                    if elem.tag == GENERIC + 'SeriesKey':
                        codes = {}
                        for value in elem.iter(GENERIC + "Value"):
                            codes[value.get('id')] = value.get('value')
                    elif elem.tag == GENERIC + 'Obs':
                        for elem1 in elem.iterchildren():
                            observation_status = 'A'
                            if elem1.tag == GENERIC + 'ObsDimension':
                                dimension = elem1.get('value')
                            elif elem1.tag == GENERIC + 'ObsValue':
                                value = elem1.get('value')
                            elif elem1.tag == GENERIC + 'Attibutes':
                                for elem2 in elem1.iter(".//generic:Value[@id='OBS_STATUS']",
                                    namespaces=tree.nsmap):
                                    observation_status = elem2.get('value')
                        raw_dates.append(dimension)
                        raw_values.append(value)
                        raw_status.append(observation_status)
                dates = PD.to_datetime(raw_dates)
                value_series = PD.TimeSeries(raw_values, index = dates, dtype = datatype, name = codes)
                series_list.append(value_series)
                
        elif self.version == '2_0':
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
            url = '/'.join([self.sdmx_url,query])
            tree = self.get_tree(url)

            for series in tree.iterfind(".//generic:Series",
                                             namespaces=tree.nsmap):
                raw_dates = []
                raw_values = []
                raw_status = []
                
                codes = {}
                for codes_ in series.iterfind(".//generic:SeriesKey",
                                           namespaces=tree.nsmap):
                    for key in codes_.iterfind(".//generic:Value",
                                               namespaces=tree.nsmap):
                        codes[key.get('concept')] = key.get('value')
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

                        raw_dates.append(dimension)
                        raw_values.append(value)
                        raw_status.append(observation_status)
                dates = PD.to_datetime(raw_dates)
                value_series = PD.TimeSeries(raw_values, index = dates, dtype = datatype, name = codes)
                series_list.append(value_series)
              
        else: raise ValueError("SDMX version must be either '2_0' or '2_1'. %s given." % self.version)
        # Handle empty lists
        if series_list == []: 
            if concat:
                return PD.DataFrame(), {}
            else:
                return [], {}
            
        # Prepare the codes, remove global codes applying to all series.
        code_sets = {k : list(set([s.name[k] for s in series_list])) 
                     for k in series_list[0].name}
            
        global_codes = {k : code_sets[k][0] for k in code_sets 
                            if len(code_sets[k]) == 1}
        # Remove global codes as they should not lead to index levels in the DataFrame 
        for k in global_codes: code_sets.pop(k)
        
        if type(concat) == bool:
            # Sort the keys with llargest set first unless concat defines the order through a list. 
            lengths = [(len(code_sets[k]), k) for k in code_sets]
            lengths.sort(reverse = True)
            sorted_keys = [k[1] for k in lengths]
        else: # so concat must be a list containing exactly the non-global keys in the desired order
            # Remove any global codes from the list
            sorted_keys = [k for k in concat if k not in global_codes.keys()] 
        if concat:    
            # Construct the multi-index from the Cartesian product of the sets.
            # This may generate too many columns if not all possible 
            # tuples are needed. But it seems very difficult to construct a
            # minimal multi-index from the series_list.
            
            column_index = PD.MultiIndex.from_product(
                [code_sets[k] for k in sorted_keys])
            column_index.names = sorted_keys 
            df = PD.DataFrame(columns = column_index, index = series_list[0].index)
                # Add the series to the DataFrame. Generate column keys from the metadata        
            for s in series_list:
                column_pos = [s.name[k] for k in sorted_keys]
                # s.name = None 
                df[tuple(column_pos)] = s
            return df, global_codes
            
        else:
            # Create a list of Series
            # Prepare the sorted metadata of each series
            for s in series_list:
                for k in global_codes: s.name.pop(k)
                s.name = to_namedtuple([(k, s.name[k]) for k in sorted_keys])             
            return series_list, global_codes
    
    
eurostat = SDMX_REST('http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest',
                     '2_1','ESTAT')
eurostat_test = SDMX_REST('http://localhost:8800/eurostat',
                     '2_1','ESTAT')
ecb = SDMX_REST('http://sdw-ws.ecb.europa.eu',
                     '2_0','ECB')
ilo = SDMX_REST('http://www.ilo.org/ilostat/sdmx/ws/rest/',
                     '2_1','ILO')
fao = SDMX_REST('http://data.fao.org/sdmx',
                     '2_1','FAO')

# This is for easier testing during development. Run it as a script. 
# Play around with the args concat, to_file and from_file, and remove this line before release.
# d, meta =eurostat.data('ei_nagt_q_r2', '', concat = True, from_file = 'ESTAT.sdmx')  
conn = eurostat.dataflows()
# conn = ecb.dataflows()
