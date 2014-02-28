#! /usr/bin/env python3
# -*- coding: utf-8 -*-
""" Python interface to SDMX """

from suds.client import Client
import datetime
import requests
import json
import lxml.etree

#Utter failure with suds and the SOAP interface. Can anybody explain this to me
#client = Client("http://ec.europa.eu/eurostat/SDMX/diss-ws/SdmxServiceService?wsdl")
#GetDataflow = client.factory.create('GetDataflow')
#GetDataflow.DataflowQuery.Header.ID = "QUERY"
#GetDataflow.DataflowQuery.Header.Test = False
#today = datetime.date.today().strftime('%Y-%m-%d')
#GetDataflow.DataflowQuery.Header.Prepared = today
#GetDataflow.DataflowQuery.Header.Sender = "Michael"
#GetDataflow.DataflowQuery.Header.DataProvider = "ESTAT"

class SDMX_ML(object):
    def __init__(self,SDMXML):
        self.SDMXML = SDMXML


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
            self._dataflow = requests.get(self.sdmx_url+'/'
                                          +resource+'/'
                                          +self.agencyID+'/'
                                          +resourceID+'/'
                                          +version)
            self._dataflow = self._dataflow.text.encode('utf-8')
            parser = lxml.etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
            print(self._dataflow)
            self._dataflow = lxml.etree.fromstring(self._dataflow, parser=parser)
        return self._dataflow

    def data_extraction(self, flowRef, key, startperiod, endperiod):
        resource = 'data'
        request = requests.get(self.sdmx_url+'/'
                               +resource+'/'
                               +flowRef+'/'
                               +key
                               +'?startperiod='+startperiod
                               +'&endPeriod='+endperiod)
        xml_response = request.text.encode('utf-8')
        parser = lxml.etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        SDMXML = lxml.etree.fromstring(xml_response, parser=parser)
        return SDMXML

eurostat = SDMX_REST("http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest", 'ESTAT')
