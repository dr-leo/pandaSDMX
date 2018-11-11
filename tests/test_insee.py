# -*- coding: utf-8 -*-
from collections import OrderedDict

import pandasdmx
from pandasdmx import Request
import pytest

from . import test_data_path


test_data_path = test_data_path / 'insee'

DATAFLOW_FP = test_data_path / 'insee-dataflow.xml'

DATASETS = {
    'IPI-2010-A21': {
        'data-fp': test_data_path / 'insee-IPI-2010-A21-data.xml',
        'datastructure-fp': (test_data_path /
                             'insee-IPI-2010-A21-datastructure.xml'),
        'series_count': 20,
    },
    'CNA-2010-CONSO-SI-A17': {
        'data-fp': test_data_path / 'insee-bug-data-namedtuple.xml',
        'datastructure-fp': (test_data_path /
                             'insee-bug-data-namedtuple-datastructure.xml'),
        'series_count': 1,
    },
}

SERIES = {
    'UNEMPLOYMENT_CAT_A_B_C': {
        'data-fp': test_data_path / 'insee-bug-series-freq-data.xml',
    }
}


class TestINSEE:
    @pytest.fixture(scope='class')
    def req(self):
        return Request('INSEE')

    def test_load_dataset(self, req):
        dataset_code = 'IPI-2010-A21'

        '''load all dataflows'''
        dataflows_response = pandasdmx.open_file(DATAFLOW_FP)
        dataflows = dataflows_response.dataflow

        assert len(dataflows) == 663
        assert dataset_code in dataflows

        '''load datastructure for current dataset_code'''
        fp_datastructure = DATASETS[dataset_code]['datastructure-fp']
        datastructure_response = pandasdmx.open_file(fp_datastructure)
        assert dataset_code in datastructure_response.dataflow
        dsd = datastructure_response.dataflow[dataset_code].structure

        '''Verify dimensions list'''
        dimensions = OrderedDict([dim.id, dim] for dim in
                                 dsd.dimensions if dim.id not in
                                 ['TIME', 'TIME_PERIOD'])
        dim_keys = list(dimensions.keys())
        assert dim_keys == ['FREQ', 'PRODUIT', 'NATURE']

        '''load datas for the current dataset'''
        fp_data = DATASETS[dataset_code]['data-fp']
        data = pandasdmx.open_file(fp_data)

        '''Verify series count and values'''
        # CHANGED: dataset index added; list() not required
        series = data.data[0].series
        series_count = len(series)
        assert series_count == DATASETS[dataset_code]['series_count']

        first_series = series[0]
        observations = first_series

        first_obs = observations[0]
        last_obs = observations[-1]

        assert first_obs.dim == '2015-10'
        assert first_obs.value == '105.61'

        assert last_obs.dim == '1990-01'
        assert last_obs.value == '139.22'

    def test_fixe_key_names(self, req):
        """Verify key or attribute contains '-' in name
        """
        dataset_code = 'CNA-2010-CONSO-SI-A17'

        fp_datastructure = DATASETS[dataset_code]['datastructure-fp']
        datastructure_response = pandasdmx.open_file(fp_datastructure)
        assert dataset_code in datastructure_response.dataflow
        dsd = datastructure_response.dataflow[dataset_code].structure

        dimensions = OrderedDict([dim.id, dim] for dim in
                                 dsd.dimensions if dim.id not in
                                 ['TIME', 'TIME_PERIOD'])
        dim_keys = list(dimensions.keys())
        assert dim_keys == ['SECT-INST', 'OPERATION', 'PRODUIT', 'PRIX']

        fp_data = DATASETS[dataset_code]['data-fp']
        data = pandasdmx.open_file(fp_data)

        # CHANGED: dataset index added; list() not required
        series = data.data[0].series

        series_key = list(series.keys())[0]

        assert (list(series_key.values.keys()) ==
                ['SECT-INST', 'OPERATION', 'PRODUIT', 'PRIX'])

        assert (list(series_key.attrib.keys()) ==
                ['FREQ', 'IDBANK', 'TITLE', 'LAST_UPDATE', 'UNIT_MEASURE',
                 'UNIT_MULT', 'REF_AREA', 'DECIMALS', 'BASE_PER',
                 'TIME_PER_COLLECT'])

    def test_freq_in_series_attribute(self, req):
        # Test that we don't have regression on Issues #39 and #41
        # INSEE time series provide the FREQ value as attribute on the series
        # instead of a dimension. This caused a runtime error when writing as
        # pandas dataframe.
        data_response = pandasdmx.open_file(
            SERIES['UNEMPLOYMENT_CAT_A_B_C']['data-fp'])
        pandasdmx.to_pandas(data_response)
