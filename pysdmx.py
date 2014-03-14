#! /usr/bin/env python3
# -*- coding: utf-8 -*-
""" Python interface to SDMX """

import requests
import pandas
import lxml.etree
import uuid
import datetime
import numpy

def date_parser(date, frequency):
    if frequency == 'A':
        return datetime.datetime.strptime(date, '%Y')
    if frequency == 'Q':
        date = date.split('Q')
        date = str(int(date[1])*3) + date[0]
        return datetime.datetime.strptime(date, '%m%Y')
    if frequency == 'M':
        return datetime.datetime.strptime(date, '%YM%m')


def query_rest(url):
 
    request = requests.get(url, timeout= 20)
    if request.status_code != requests.codes.ok:
        raise ValueError("Error getting client({})".format(request.status_code))      
    parser = lxml.etree.XMLParser(
        ns_clean=True, recover=True, encoding='utf-8')
    return lxml.etree.fromstring(
        request.text.encode('utf-8'), parser=parser)


class Data(object):
    def __init__(self, SDMXML):
        self.tree = SDMXML
        self._time_series = None

    @property
    def time_series(self):
        if not self._time_series:
            self._time_series = {}
            for series in self.tree.iterfind(".//generic:Series",
                                             namespaces=self.tree.nsmap):
                codes = {}
                for key in series.iterfind(".//generic:Value",
                                           namespaces=self.tree.nsmap):
                    codes[key.get('id')] = key.get('value')
                time_series_ = []
                for observation in series.iterfind(".//generic:Obs",
                                                   namespaces=self.tree.nsmap):
                    dimensions = observation.xpath(".//generic:ObsDimension",
                                                   namespaces=self.tree.nsmap)
                    dimension = dimensions[0].values()
                    dimension = date_parser(dimension[0], codes['FREQ'])
                    values = observation.xpath(".//generic:ObsValue",
                                               namespaces=self.tree.nsmap)
                    value = values[0].values()
                    value = value[0]
                    observation_status = 'A'
                    for attribute in \
                        observation.iterfind(".//generic:Attributes",
                                             namespaces=self.tree.nsmap):
                        for observation_status_ in \
                            attribute.xpath(
                                ".//generic:Value[@id='OBS_STATUS']",
                                namespaces=self.tree.nsmap):
                            if observation_status_ is not None:
                                observation_status \
                                    = observation_status_.get('value')
                    time_series_.append((dimension, value, observation_status))
                time_series_.sort()
                dates = numpy.array(
                    [observation[0] for observation in time_series_])
                values = numpy.array(
                    [observation[1] for observation in time_series_])
                time_series_ = pandas.Series(values, index=dates)
                self._time_series[str(uuid.uuid1())] = (codes, time_series_)
        return self._time_series


class DSD(object):
    def __init__(self, SDMXML):
        self.tree = SDMXML
        self._codes = None

    @property
    def codes(self):
        if not self._codes:
            self._codes = {}
            codelists = self.tree.xpath(".//str:Codelists",
                                          namespaces=self.tree.nsmap)
            for codelists_ in codelists:
                for codelist in codelists_.iterfind(".//str:Codelist",
                                                    namespaces=self.tree.nsmap):
                    name = codelist.xpath('.//com:Name', namespaces=self.tree.nsmap)
                    name = name[0]
                    name = name.text
                    code = []
                    for code_ in codelist.iterfind(".//str:Code",
                                                   namespaces=self.tree.nsmap):
                        code_key = code_.get('id')
                        code_name = code_.xpath('.//com:Name',
                                                namespaces=self.tree.nsmap)
                        code_name = code_name[0]
                        code.append((code_key,code_name.text))
                    self._codes[name] = code
        return self._codes


class Dataflows(object):
    def __init__(self, SDMXML):
        self.tree = SDMXML
        self._all_dataflows = None

    @property
    def all_dataflows(self):
        if not self._all_dataflows:
            self._all_dataflows = {}
            for dataflow in self.tree.iterfind(".//str:Dataflow",
                                               namespaces=self.tree.nsmap):
                id = dataflow.get('id')
                agencyID = dataflow.get('agencyID')
                version = dataflow.get('version')
                titles = {}
                for title in dataflow.iterfind(".//com:Name",
                                               namespaces=self.tree.nsmap):
                    language = title.values()
                    language = language[0]
                    titles[language] = title.text
                self._all_dataflows[id] = (agencyID, version, titles)
        return self._all_dataflows


class SDMX_REST(object):
    def __init__(self, sdmx_url, agencyID):
        self.sdmx_url = sdmx_url
        self.agencyID = agencyID
        self._dataflow = None

    @property
    def dataflow(self):
        if not self._dataflow:
            resource = 'dataflow'
            resourceID = 'all'
            version = 'latest'
            url = (self.sdmx_url + '/'
                   + resource + '/'
                   + self.agencyID + '/'
                   + resourceID + '/'
                   + version)
            self._dataflow = Dataflows(query_rest(url))
        return self._dataflow

    def data_definition(self, flowRef):
        resource = 'datastructure'
        url = (self.sdmx_url + '/'
               + resource + '/'
               + self.agencyID + '/'
               + 'DSD_'
               + flowRef)
        return DSD(query_rest(url))

    def data_extraction(self, flowRef, key, startperiod=None, endperiod=None):
        resource = 'data'
		if startperiod is not None and endperiod is not None:
			query = self.sdmx_url + '/'
               + resource + '/'
               + flowRef + '/'
               + key
               + '?startperiod=' + startperiod
               + '&endPeriod=' + endperiod
		else:
			query = self.sdmx_url + '/'
               + resource + '/'
               + flowRef + '/'
               + key
        url = (query)
        return Data(query_rest(url))


eurostat = SDMX_REST('http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest',
                     'ESTAT')
