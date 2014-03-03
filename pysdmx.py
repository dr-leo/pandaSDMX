#! /usr/bin/env python3
# -*- coding: utf-8 -*-
""" Python interface to SDMX """

import requests
import lxml.etree
import uuid

#Utter failure with suds and the SOAP interface. Can anybody explain this to me
#client = Client("http://ec.europa.eu/eurostat/SDMX/diss-ws/SdmxServiceService?wsdl")
#GetDataflow = client.factory.create('GetDataflow')
#GetDataflow.DataflowQuery.Header.ID = "QUERY"
#GetDataflow.DataflowQuery.Header.Test = False
#today = datetime.date.today().strftime('%Y-%m-%d')
#GetDataflow.DataflowQuery.Header.Prepared = today
#GetDataflow.DataflowQuery.Header.Sender = "Michael"
#GetDataflow.DataflowQuery.Header.DataProvider = "ESTAT"


def query_rest(url):
	request = requests.get(url)
	parser = lxml.etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
	return lxml.etree.fromstring(request.text.encode('utf-8'), parser=parser)

class Data(object):
    def __init__(self,SDMXML):
        self.tree = SDMXML
        self._time_series = None
    @property
    def time_series(self):
        if not self._time_series:
            self._time_series = {}
            for series in self.tree.iterfind(".//generic:Series",namespaces=self.tree.nsmap):
                codes = {}
                for key in series.iterfind(".//generic:Value",namespaces=self.tree.nsmap):
                    codes[key.get('id')] = key.get('value')
                observations = []
                for observation in series.iterfind(".//generic:Obs",namespaces=self.tree.nsmap):
                    dimensions = observation.xpath(".//generic:ObsDimension",namespaces=self.tree.nsmap)
                    dimension = dimensions[0].values()
                    dimension = dimension[0]
                    values = observation.xpath(".//generic:ObsValue",namespaces=self.tree.nsmap)
                    value = values[0].values()
                    value = value[0]
                    observation_status = 'A'
                    for attribute in observation.iterfind(".//generic:Attributes",namespaces=self.tree.nsmap):
                        for observation_status_ in attribute.xpath(".//generic:Value[@id='OBS_STATUS']",namespaces=self.tree.nsmap):
                            if observation_status_ != None:
                                observation_status = observation_status_.get('value')
                    observations.append((dimension, value,observation_status))
                self._time_series[str(uuid.uuid1())] = (codes,observations)
                print([(observation[0],observation[1]) for observation in observations])
        return  self._time_series

class Dataflows(object):
    def __init__(self,SDMXML):
        self.tree = SDMXML
        self._all_dataflows = None

    @property
    def all_dataflows(self):
        if not self._all_dataflows:
            self._all_dataflows = {}
            for dataflow in self.tree.iterfind(".//str:Dataflow", namespaces=self.tree.nsmap):
                id = dataflow.get('id')
                agencyID = dataflow.get('agencyID')
                version = dataflow.get('version')
                titles = {}
                for title in dataflow.iterfind(".//com:Name", namespaces=self.tree.nsmap):
                    language = title.values()
                    language = language[0]
                    titles[language] = title.text
                self._all_dataflows[id] = (agencyID, version, titles)
        return self._all_dataflows



class SDMX_REST(object):
    def __init__(self,sdmx_url,agencyID):
        self.sdmx_url = sdmx_url
        self.agencyID = agencyID
        self._dataflow = None

    @property
    def dataflow(self):
        if not self._dataflow:
            resource = 'dataflow'
            resourceID = 'all'
            version = 'latest'
            url = (self.sdmx_url+'/'
                               +resource+'/'
                               +self.agencyID+'/'
                               +resourceID+'/'
                               +version)
            self._dataflow = Dataflows(query_rest(url))
        return self._dataflow

    def data_extraction(self, flowRef, key, startperiod, endperiod):
        resource = 'data'
        url = (self.sdmx_url+'/'
                           +resource+'/'
                           +flowRef+'/'
                           +key
                           +'?startperiod='+startperiod
                           +'&endPeriod='+endperiod)
        return Data(query_rest(url))

eurostat = SDMX_REST('http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest','ESTAT')
