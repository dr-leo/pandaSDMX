'''
.. module:: pandasdmx
    
    :synopsis: A Python- and pandas-powered client for statistical data and metadata exchange 
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; forked from http://github.com/widukind/pysdmx
'''
# uncomment this for debugging and use embed() to invoke an ipython shell
from IPython import embed

import requests
import pandas as PD
import numpy as NP
import lxml.etree
import sqlite3
from io import BytesIO
import re, zipfile, time
from collections import OrderedDict, namedtuple


__all__ = ['client', 'Client']

# Allow easy checking for existing namedtuple classes that can be reused for column metadata  
tuple_classes = []

def to_namedtuple(mapping):
    """
    Convert a list of (key,value) tuples into a namedtuple. 
    If there is not already 
    a suitable class in 'tuple_classes', Create a new class first 
    and append it to the list.
        
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
            
        
               
class Client:
    """Data provider. This is the main class that allows practical access to all the data.

    :ivar sdmx_url: The URL of the SDMX endpoint, the webservice employed to access the data.
    :type sdmx_url: str
    :ivar agencyID: An identifier of the statistical provider.
    :type agencyID: str
    :param: db_filename: filename of the local database for dataflows. 
    Default: ':memory:' for an sqlite in-memory database
    """
    def __init__(self, sdmx_url, version, agencyID, db_filename = ':memory:'):
        self.sdmx_url = sdmx_url
        self.agencyID = agencyID
        self.version = version
        self.db_filename = db_filename
        self.db = None # database connector


    def __repr__(self):
        return ''.join((str(self.__class__), "('", self.sdmx_url, "', '",
            self.agencyID, "', db_filename = '", str(self.db_filename), "')"))
         
    def __str__(self):
        if self.db:
            table_list = self.db.execute(
                    'SELECT * FROM SQLITE_MASTER').fetchall()
        else: table_list = []
        return ''.join((self.__repr__(), ' Database: ', 
            str(self.db), ' ', str((
                ['table: ' + t['tbl_name'] + ' SQL: ' + 
                t['sql'] + '; ' for t in table_list] or ''))))
             
    def __del__(self):
        if self.db: self.db.close()
        
                     
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
            ns_clean=True, recover=True)
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
        
        response = requests.get(url, timeout= 40)
        
        if response.status_code == requests.codes.ok:
            xml_str = response.content
            embed()
        elif response.status_code == 430:
            #Sometimes, eurostat creates a zipfile when the query is too large. We have to wait for the file to be generated.
            parser = lxml.etree.XMLParser(
                                          ns_clean=True, recover=True)
            tree = lxml.etree.fromstring(xml_str, parser = parser)
            messages = tree.xpath('.//footer:Message/common:Text',
                                      namespaces = tree.nsmap)
            regex_ = re.compile("Due to the large query the response will be written "
                                "to a file which will be located under URL: (.*)")
            matches = [regex_.match(element.text) for element in messages]
            if matches:
                xml_str = None
                i = 30
                while i < 51:
                    time.sleep(i)
                    i = i+10
                    url = matches[0].groups()[0]
                    response = requests.get(url)
                    if response.headers['content-type'] == "application/octet-stream":
                        buffer = BytesIO(response.content)
                        file = zipfile.ZipFile(buffer)
                        filename = file.namelist()[0]
                        xml_str = file.read(filename)
                        break
                if xml_str is None:
                    raise requests.exceptions.HTTPError("The SDMX server didn't provide the requested file. Error code: {0}" 
                                                            .format(response.status_code))
            else:
                raise requests.exceptions.HTTPError(
                        "SDMX server returned an error message. Code: {0}"
                        .format(response.status_code))      
        else:
            raise requests.exceptions.HTTPError("SDMX server returned an error message. Code: {0}"
                    .format(response.status_code))      
        return xml_str
    
    
    def _init_database(self, tablename):
        '''
        Helper method to initialize database.
        Called by dataflows()
        Return: sqlite3.Connection
        '''
        if not self.db:
            self.db = sqlite3.connect(self.db_filename)
            self.db.row_factory = sqlite3.Row
        self.db.execute(u'''CREATE TABLE IF NOT EXISTS {0} 
            (id INTEGER PRIMARY KEY, agencyID text, flowref text, version text, title text)'''.format( 
            tablename))
        # Delete any pre-existing rows
        anyrows = self.db.execute('SELECT * FROM {0}'.format(
            tablename)).fetchone()
        if anyrows:
            self.db.execute('DELETE FROM {0}'.format(tablename))
        return self.db

    def get_dataflows(self, language = 'en', to_file = None, from_file = None,
                  to_database = True, table = None):
        """
        Get list of available dataflows 
        Arguments:
        :param: language: keyword argument specifying the language of the 
        dataflow titles to be stored. This feature is not supported by 
        SDMX 2.0. Defaults to 'en' for English.
        :type: str
        :param: to_file: keyword argument specifying the filename of a file 
        to write the dataflows list in xml-format.  
        :type: str
        :param: 'from_file': Read the xml data from an xml file rather than 
        requesting the xml data via http from the data provider. 
        By convention, 'from_file' should have the 
        extension '.xml'.     
        :param: to_database: if True (default), the received dataflows are 
        stored in a database in the table. The 'table' keyword argument specifies
        the table's name. The instance variable
        self.db is a connector to the database. It is also returned. 
        If the database connection in self.db is None, it is first opened.
        :type: str   
        :param: table: name of the table into which the dataflow descriptions will be inserted.
        If the database does not contain a table of this name, it is first created.
        If it does, that table is dropped first. Hence, append is not supported.
        Defaults to self.agencyID + '_dataflows'
        :type: str 
     
        return: sqlite3.Connection or None (if data is written to '.xml' file
        """
        
        
        if not table: table = self.agencyID + '_dataflows' # default value for table name 
            
        if self.version == '2_1':
            url = '/'.join([self.sdmx_url, 'dataflow', self.agencyID, 'all', 'latest'])
            tree = self.get_tree(url, to_file = to_file, from_file = from_file)
             
            # Init the database and store the parsed data in it 
            if to_database: 
                self._init_database(table)
                cur = self.db.cursor()
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
                        if descr_lang == language: 
                            row = ('"' + agencyID + '"', '"' + flowref + '"', 
                                   version, '"' + title.text + '"')
                            cur.execute(u'''INSERT INTO     {0} VALUES 
                            (NULL, {1[0]}, {1[1]}, {1[2]}, {1[3]})'''.format(
                                           table, row))
                    
        elif self.version == '2_0':
            url = '/'.join([self.sdmx_url, 'Dataflow'])
            tree = self.get_tree(url, to_file = to_file, from_file = from_file)
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
                        
        self.db.commit()
        return self.db 

    def get_codes(self, flowRef, to_file = None, from_file = None):
        """Data definitions

        Returns a dictionnary describing the available dimensions for a specific flowRef.

        :param flowRef: Identifier of the dataflow
        :type flowRef: str or sqlite3.Row
        :return: OrderedDict"""
        if isinstance(flowRef, sqlite3.Row):
            flowRef = flowRef['flowref']
        if self.version == '2_1':
            url = '/'.join([self.sdmx_url, 'datastructure', self.agencyID, 'DSD_' + flowRef])
            tree = self.get_tree(url, to_file = to_file, from_file = from_file)
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
            tree = self.get_tree(url)
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


    def get_data(self, flowRef, key, startperiod=None, endperiod=None, 
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
            flowRef = flowRef['flowref']
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
                if 'FREQ' in codes:
                    if codes['FREQ'] == 'A':
                        freq_str = 'Y'
                    else: 
                        freq_str = codes['FREQ']
                    dates = PD.PeriodIndex(raw_dates, freq = freq_str)
                else:
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
                if 'FREQ' in codes:
                    if codes['FREQ'] == 'A':
                        freq_str = 'Y'
                    else: 
                        freq_str = codes['FREQ']
                    dates = PD.PeriodIndex(raw_dates, freq = freq_str)
                else:
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
    
providers = {
    'Eurostat' : ('http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest',
                    '2_1','ESTAT'),
    'ECB' : ('http://sdw-ws.ecb.europa.eu',
                     '2_0','ECB'),
    'ILO' : ('http://www.ilo.org/ilostat/sdmx/ws/rest/',
                            '2_1','ILO'),
    'FAO' : ('http://data.fao.org/sdmx',
                     '2_1','FAO')
    }    

def client(name, db_filename = ':memory:'):
    '''
    'Client' factory (convenience function).
    Usage: my_client = client(<provider_name>, <database_filename>)
    To get standard provider names, print(sdmx.providers.keys())
    'database_filename defaults to ':memory:' for an in-memory SQLite db.
    ''' 
    return Client(*providers[name], db_filename = db_filename)

        