    #! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. module:: pysdmx
    :platform: Unix, Windows
    :synopsis: Python interface for SDMX

.. :moduleauthor :: Widukind team <widukind-dev@cepremap.org>
"""

import requests
import pandas
import lxml.etree
import datetime
from io import BytesIO
import re
import zipfile
import time
from collections import OrderedDict, namedtuple


# Allow easy checking for existing namedtuple classes that can be reused for column metadata  
tuple_classes = []

def to_namedtuple(codes):
    """
    Convert a dict into a namedtuple. If there is not already 
    a suitable class in 'tuple_classes', Create a new class first and append it to the list.
        
    return a namedtuple instance
    """

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
            
        
        
        
def date_parser(date, frequency):
    """Generate proper index for pandas

    :param date: A date
    :type date: str
    :param frequency: A frequency as specified in SDMX, A for Annual, Q for Quarterly, M for Monthly and D for Daily
    :type frequency: str
    :return: datetime.datetime()

    >>> date_parser('1987-02-02','D')
    datetime.datetime(1987, 2, 2, 0, 0)
    """

    if frequency == 'A':
        return datetime.datetime.strptime(date, '%Y')
    if frequency == 'Q':
        date = date.split('-Q')
        date = str(int(date[1])*3) + date[0]
        return datetime.datetime.strptime(date, '%m%Y')
    if frequency == 'M':
        return datetime.datetime.strptime(date, '%Y-%m')
    if frequency == 'D':
        return datetime.datetime.strptime(date, '%Y-%m-%d')


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
        self._dataflows = None
        self.version = version

    
    def query_rest(self, url, to_file = None, from_file = None):
        """Retrieve SDMX messages.

        :param url: The URL of the message.
        :type url: str
        :return: An lxml.etree.ElementTree() of the SDMX message
        """
        parser = lxml.etree.XMLParser(
            ns_clean=True, recover=True, encoding='utf-8')
        if from_file:
            # Load data from local file and parse it. 
            with open(from_file, 'b') as f:
                return lxml.etree.fromstring(f.read(), parser = parser) 
                    
        # Fetch data from the provider    
        request = requests.get(url, timeout= 20)
        if request.status_code == requests.codes.ok:
            response_str = request.text.encode('utf-8')
            response = lxml.etree.fromstring(response_str, parser = parser)
        elif request.status_code == 430:
            #Sometimes, eurostat creates a zipfile when the query is too large. We have to wait for the file to be generated.
            messages = response.xpath('.//footer:Message/common:Text',
                                      namespaces=response.nsmap)
            regex_ = re.compile("Due to the large query the response will be written "
                                "to a file which will be located under URL: (.*)")
            matches = [regex_.match(element.text) for element in messages]
            if bool(matches):
                response_ = None
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
                        response_str = file.read(filename)
                        response_ = lxml.etree.fromstring(response_str, parser = parser)
                        break
                        if response_ is None:
                            raise Exception("The provider has not delivered the file you are looking for.")
            else:
                raise ValueError("Error getting client({})".format(request.status_code))      
        else:
            raise ValueError("Error getting client({})".format(request.status_code))
        if to_file:
            if not isinstance(to_file, bool): # so it must be str or unicode
                filename = to_file
            else:
                filename = self.agencyID + '.sdmx'
            with open(filename, 'wb') as f:
                f.write(response_str)
                                     
        return response

    @property
    def dataflows(self):
        """Index of available dataflows

        :type: dict"""
        if not self._dataflows:
            if self.version == '2_1':
                url = '/'.join([self.sdmx_url, 'dataflow', self.agencyID, 'all', 'latest'])
                tree = self.query_rest(url)
                dataflow_path = ".//str:Dataflow"
                name_path = ".//com:Name"
                if not self._dataflows:
                    self._dataflows = {}
                    for dataflow in tree.iterfind(dataflow_path,
                                                       namespaces=tree.nsmap):
                        id = dataflow.get('id')
                        agencyID = dataflow.get('agencyID')
                        version = dataflow.get('version')
                        titles = {}
                        for title in dataflow.iterfind(name_path,
                                                       namespaces=tree.nsmap):
                            language = title.values()
                            language = language[0]
                            titles[language] = title.text
                        self._dataflows[id] = (agencyID, version, titles)
            if self.version == '2_0':
                url = '/'.join([self.sdmx_url, 'Dataflow'])
                tree = self.query_rest(url)
                dataflow_path = ".//structure:Dataflow"
                name_path = ".//structure:Name"
                keyid_path = ".//structure:KeyFamilyID"
                if not self._dataflows:
                    self._dataflows = {}
                    for dataflow in tree.iterfind(dataflow_path,
                                                       namespaces=tree.nsmap):
                        for id in dataflow.iterfind(keyid_path,
                                                       namespaces=tree.nsmap):
                            id = id.text
                        agencyID = dataflow.get('agencyID')
                        version = dataflow.get('version')
                        titles = {}
                        for title in dataflow.iterfind(name_path,
                                                       namespaces=tree.nsmap):
                            titles['en'] = title.text
                        self._dataflows[id] = (agencyID, version, titles)
        return self._dataflows

    def codes(self, flowRef):
        """Data definitions

        Returns a dictionnary describing the available dimensions for a specific flowRef.

        :param flowRef: Identifier of the dataflow
        :type flowRef: str
        :return: dict"""
        if self.version == '2_1':
            url = '/'.join([self.sdmx_url, 'datastructure', self.agencyID, 'DSD_' + flowRef])
            tree = self.query_rest(url)
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
            tree = self.query_rest(url)
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
        with_status = False, concat = False):
        """Get data

        :param flowRef: an identifier of the data
        :type flowRef: str
        :param key: a filter using codes (for example, .... for no filter ...BE for all the series related to Belgium) if using v2_1. In 2_0, you should be providing a dict following that syntax {dimension:value}
        :type key: str or dict
        :param startperiod: the starting date of the time series that will be downloaded (optional, default: None)
        :type startperiod: datetime.datetime()
        :param endperiod: the ending date of the time series that will be downloaded (optional, default: None)
        :type endperiod: datetime.datetime()
        :return: DataFrame whose column index are namedtuples storing the full metadata.
        """
       
        series_list = [] 
        
        if self.    version == '2_1':
            resource = 'data'
            if startperiod and endperiod:
                query = '/'.join([resource, flowRef, key
                        + '?startperiod=' + startperiod
                        + '&endPeriod=' + endperiod])
            else:
                query = '/'.join([resource, flowRef, key])
            url = '/'.join([self.sdmx_url,query])
            tree = self.query_rest(url, to_file = to_file)
            GENERIC = '{'+tree.nsmap['generic']+'}'
            
            for series in tree.iterfind(".//generic:Series",
                                             namespaces=tree.nsmap):
                raw_dates = []
                raw_values = []
                raw_status = []
                
                for elem in series.iterchildren():
                    
                    if elem.tag == GENERIC + 'SeriesKey':
                        codes = OrderedDict()
                        for value in elem.iter(GENERIC + "Value"):
                            codes[value.get('id')] = value.get('value')
                    elif elem.tag == GENERIC + 'Obs':
                        for elem1 in elem.iterchildren():
                            observation_status = 'A'
                            if elem1.tag == GENERIC + 'ObsDimension':
                                dimension = elem1.get('value')
                                dimension = date_parser(dimension, codes['FREQ'])
                            elif elem1.tag == GENERIC + 'ObsValue':
                                value = elem1.get('value')
                            elif elem1.tag == GENERIC + 'Attibutes':
                                for elem2 in elem1.iter(".//generic:Value[@id='OBS_STATUS']",
                                    namespaces=tree.nsmap):
                                    observation_status = elem2.get('value')
                        raw_dates.append(dimension)
                        raw_values.append(value)
                        raw_status.append(observation_status)
                dates = pandas.to_datetime(raw_dates)
                metadata = to_namedtuple(codes)
                value_series = pandas.TimeSeries(raw_values, index = dates, dtype = 'float64')
                if with_status:
                    col_index = pandas.MultiIndex(
                        levels = [[metadata], ['values', 'status']],
                        labels = [[0, 0], [0, 1]])
                    list_item = pandas.DataFrame([value_series, raw_status], 
                        columns = col_index)
                else:
                    value_series.name = metadata
                    list_item = value_series
                series_list.append(list_item) 
                
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
            tree = self.query_rest(url)
            _time_series = []
            _metadata = []
            for series in tree.iterfind(".//generic:Series",
                                             namespaces=tree.nsmap):
                raw_dates = []
                raw_values = []
                raw_status = []
                
                codes = OrderedDict()
                for codes_ in series.iterfind(".//generic:SeriesKey",
                                           namespaces=tree.nsmap):
                    for key in codes_.iterfind(".//generic:Value",
                                               namespaces=tree.nsmap):
                        codes[key.get('concept')] = key.get('value')
                for observation in series.iterfind(".//generic:Obs",
                                                   namespaces=tree.nsmap):
                    dimensions = observation.xpath(".//generic:Time",
                                                   namespaces=tree.nsmap)
                    dimension = date_parser(dimensions[0].text, codes['FREQ'])
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
                    
                dates = pandas.to_datetime(raw_dates)
                code_tuple = to_namedtuple(codes)
                series_ = pandas.DataFrame(raw_values, index = dates)
                df[code_tuple] = series_ 

        else: raise ValueError('Unsupported SDMX version: %s' % self.version)
        
        if concat: return pandas.concat(series_list, axis = 1)   
        else: return series_list

        

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

d=eurostat.data('ei_nagt_q_r2', '', concat = False, from_file = 'ESTAT.sdmx')  

