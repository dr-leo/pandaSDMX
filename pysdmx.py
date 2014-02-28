#! /usr/bin/env python3
# -*- coding: utf-8 -*-
""" Python interface to SDMX """

from suds.client import Client
import datetime
import requests
import json
import lxml.etree
import logging

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

class SDMX_ML(object):
    def __init__(self,SDMXML):
        self.SDMXML = SDMXML
	@property
	def time_series(self):
		raise NotImplementedError("Work in progress")


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
            self._dataflow = query_rest(url)
        return self._dataflow

    def data_extraction(self, flowRef, key, startperiod, endperiod):
        resource = 'data'
        url = (self.sdmx_url+'/'
					       +resource+'/'
					       +flowRef+'/'
					       +key
					       +'?startperiod='+startperiod
					       +'&endPeriod='+endperiod)
        SDMXML = query_rest(url)
        return SDMXML

eurostat = SDMX_REST("http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest", 'ESTAT')
