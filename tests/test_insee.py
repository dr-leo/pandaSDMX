# -*- coding: utf-8 -*-

import os
from collections import OrderedDict

import unittest

from pandasdmx import Request

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

RESOURCES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "data", "insee"))

DATAFLOW_FP = os.path.abspath(
    os.path.join(RESOURCES_DIR, "insee-dataflow.xml"))

DATASETS = {
    'IPI-2010-A21': {
        'data-fp': os.path.abspath(os.path.join(RESOURCES_DIR, "insee-IPI-2010-A21-data.xml")),
        'datastructure-fp': os.path.abspath(os.path.join(RESOURCES_DIR, "insee-IPI-2010-A21-datastructure.xml")),
        'series_count': 20,
    },
    'CNA-2010-CONSO-SI-A17': {
        'data-fp': os.path.abspath(os.path.join(RESOURCES_DIR, "insee-bug-data-namedtuple.xml")),
        'datastructure-fp': os.path.abspath(os.path.join(RESOURCES_DIR, "insee-bug-data-namedtuple-datastructure.xml")),
        'series_count': 1,
    },
}


class InseeTestCase(unittest.TestCase):

    # nosetests -s -v pandasdmx.tests.test_insee:InseeTestCase

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.sdmx = Request('INSEE')

    def test_load_dataset(self):

        dataset_code = 'IPI-2010-A21'

        '''load all dataflows'''
        dataflows_response = self.sdmx.get(
            resource_type='dataflow', agency='FR1', fromfile=DATAFLOW_FP)
        dataflows = dataflows_response.msg.dataflow

        self.assertEqual(len(dataflows.keys()), 663)
        self.assertTrue(dataset_code in dataflows)

        '''load datastructure for current dataset_code'''
        fp_datastructure = DATASETS[dataset_code]['datastructure-fp']
        datastructure_response = self.sdmx.get(
            resource_type='datastructure', agency='FR1', fromfile=fp_datastructure)
        self.assertTrue(
            dataset_code in datastructure_response.msg.datastructure)
        dsd = datastructure_response.msg.datastructure[dataset_code]

        '''Verify dimensions list'''
        dimensions = OrderedDict([dim.id, dim] for dim in dsd.dimensions.aslist(
        ) if dim.id not in ['TIME', 'TIME_PERIOD'])
        dim_keys = list(dimensions.keys())
        self.assertEqual(dim_keys, ['FREQ', 'PRODUIT', 'NATURE'])

        '''load datas for the current dataset'''
        fp_data = DATASETS[dataset_code]['data-fp']
        data = self.sdmx.get(
            resource_type='data', agency='FR1', fromfile=fp_data)

        '''Verify series count and values'''
        series = list(data.msg.data.series)
        series_count = len(series)
        self.assertEqual(series_count, DATASETS[dataset_code]['series_count'])

        first_series = series[0]
        observations = list(first_series.obs())

        first_obs = observations[0]
        last_obs = observations[-1]

        self.assertEqual(first_obs.dim, '2015-10')
        self.assertEqual(first_obs.value, '105.61')

        self.assertEqual(last_obs.dim, '1990-01')
        self.assertEqual(last_obs.value, '139.22')

    def test_fixe_key_names(self):
        """Verify key or attribute contains '-' in name 
        """

        dataset_code = 'CNA-2010-CONSO-SI-A17'

        fp_datastructure = DATASETS[dataset_code]['datastructure-fp']
        datastructure_response = self.sdmx.get(
            resource_type='datastructure', agency='FR1', fromfile=fp_datastructure)
        self.assertTrue(
            dataset_code in datastructure_response.msg.datastructure)
        dsd = datastructure_response.msg.datastructure[dataset_code]

        dimensions = OrderedDict([dim.id, dim] for dim in dsd.dimensions.aslist(
        ) if dim.id not in ['TIME', 'TIME_PERIOD'])
        dim_keys = list(dimensions.keys())
        self.assertEqual(
            dim_keys, ['SECT-INST', 'OPERATION', 'PRODUIT', 'PRIX'])

        fp_data = DATASETS[dataset_code]['data-fp']
        data = self.sdmx.get(
            resource_type='data', agency='FR1', fromfile=fp_data)
        series = list(data.msg.data.series)

        series = series[0]

        self.assertEqual(list(series.key._asdict().keys()),
                         ['SECT-INST', 'OPERATION', 'PRODUIT', 'PRIX'])

        self.assertEqual(list(series.attrib._asdict().keys()),
                         ['FREQ', 'IDBANK', 'TITLE', 'LAST_UPDATE', 'UNIT_MEASURE', 'UNIT_MULT', 'REF_AREA', 'DECIMALS', 'BASE_PER', 'TIME_PER_COLLECT'])
