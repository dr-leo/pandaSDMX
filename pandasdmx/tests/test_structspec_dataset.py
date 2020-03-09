from collections.abc import Mapping

import pandas as pd
import pytest

import pandasdmx as sdmx
from pandasdmx import model

from . import MessageTest, test_data_path


class StructuredMessageTest(MessageTest):
    dsd = None

    @pytest.fixture(scope='class')
    def dsd(self):
        yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]

    @pytest.fixture(scope='class')
    def msg(self, dsd):
        yield sdmx.read_sdmx(self.path.joinpath(*self.filename), dsd=dsd)


class TestStructSpecFlatDataSet(StructuredMessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_ng'
    filename = ('structured', 'ecb_exr_ng_flat.xml')
    dsd_filename = 'ecb_exr_ng_full.xml'

    def test_msg_type(self, msg):
        assert isinstance(msg.msg, model.DataMessage)

    def test_header_attributes(self, msg):
        assert msg.header.structured_by == 'STR1'
        assert msg.header.dim_at_obs == 'AllDimensions'

    def test_dataset_cls(self, msg):
        assert isinstance(msg.data[0], model.DataSet)
        assert msg.msg.data[0].dim_at_obs == 'AllDimensions'

    def test_generic_obs(self, msg):
        data = msg.data[0]
        # empty series list
        assert len(list(data.series)) == 0
        obs_list = list(data.obs())
        assert len(obs_list) == 12
        o0 = obs_list[0]
        assert len(o0) == 3
        assert isinstance(o0.key, tuple)  # obs_key
        assert o0.key.FREQ == 'M'
        assert o0.key.CURRENCY == 'CHF'
        assert o0.value == '1.3413'
        assert isinstance(o0.attrib, tuple)
        assert o0.attrib.OBS_STATUS == 'A'
        assert o0.attrib.DECIMALS == '4'

    def test_write2pandas(self, msg):
        data_series = sdmx.to_pandas(msg, attributes='')
        assert isinstance(data_series, pd.Series)


class TestStructSpecSeriesDataSet(StructuredMessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_ng'
    filename = ('structured', 'ecb_exr_ng_ts_gf.xml')
    dsd_filename = 'ecb_exr_ng_full.xml'

    def test_header_attributes(self, msg):
        assert msg.header.structured_by == 'STR1'
        assert msg.header.dim_at_obs == 'TIME_PERIOD'

    def test_dataset_cls(self, msg):
        assert isinstance(msg.data[0], model.DataSet)

    def test_obs(self, msg):
        data = msg.data[0]
        # empty obs iterator
        assert len(list(data.obs())) == 0
        series_list = list(data.series)
        assert len(series_list) == 4
        s3 = series_list[3]
        assert isinstance(s3, model.SeriesKey)
        assert isinstance(s3.key, tuple)
        assert len(s3.key) == 4
        assert s3.key.CURRENCY == 'USD'
        assert s3.attrib.DECIMALS == '4'
        obs_list = list(s3.obs)
        assert len(obs_list) == 3
        o0 = obs_list[2]
        assert len(o0) == 3
        assert o0.dim == '2010-08'
        assert o0.value == '1.2894'
        assert isinstance(o0.attrib, tuple)
        assert o0.attrib.OBS_STATUS == 'A'

    def test_pandas(self, msg):
        data = msg.data[0]
        pd_series = [s for s in sdmx.to_pandas(data, attributes='')]
        assert len(pd_series) == 4
        s3 = pd_series[3]
        assert isinstance(s3, pd.Series)
        assert s3[2] == 1.2894
        assert isinstance(s3.name, tuple)
        assert len(s3.name) == 4
        # now with attributes
        pd_series = [s for s in sdmx.to_pandas(data, attributes='osgd')]
        assert len(pd_series) == 4
        assert isinstance(pd_series[0], tuple)  # contains 2 series
        assert len(pd_series[0]) == 2
        s3, a3 = pd_series[3]
        assert isinstance(s3, pd.Series)
        assert isinstance(a3, pd.Series)
        assert s3[2] == 1.2894
        assert isinstance(s3.name, tuple)
        assert len(s3.name) == 4
        assert len(a3) == 3
        # access an attribute of the first value
        assert a3[0].OBS_STATUS == 'A'

    def test_write2pandas(self, msg):
        df = sdmx.to_pandas(msg, attributes='')
        assert isinstance(df, pd.Series)
        assert df.shape == (3, 4)
        # with metadata
        df, mdf = sdmx.to_pandas(msg, attributes='osgd')
        assert mdf.shape == (3, 4)
        assert mdf.iloc[1, 1].OBS_STATUS == 'A'


class TestStructSpecSeriesDataSet2(StructuredMessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_ng'
    filename = ('structured', 'ecb_exr_ng_ts.xml')
    dsd_filename = 'ecb_exr_ng_full.xml'

    def test_header_attributes(self, msg):
        assert msg.header.structured_by == 'STR1'
        assert msg.header.dim_at_obs == 'TIME_PERIOD'

    def test_dataset_cls(self, msg):
        assert isinstance(msg.data[0], model.DataSet)

    def test_structured_obs(self, msg):
        data = msg.data[0]
        assert len(data.obs) == 12
        series_list = list(data.series)
        assert len(series_list) == 4
        s3 = series_list[3]
        assert isinstance(s3, model.SeriesKey)
        assert isinstance(s3.key, tuple)
        assert len(s3.key) == 4
        assert s3.key.CURRENCY == 'USD'
        assert s3.attrib.DECIMALS == '4'
        obs_list = list(s3.obs)
        assert len(obs_list) == 3
        o0 = obs_list[2]
        assert len(o0) == 3
        assert o0.dim == '2010-08'
        assert o0.value == '1.2894'
        assert isinstance(o0.attrib, tuple)
        assert o0.attrib.OBS_STATUS == 'A'

    def test_dataframe(self, msg):
        data = msg.data[0]
        s = sdmx.to_pandas(data, attributes='')
        assert isinstance(s, pd.Series)
        assert len(s) == 12


class TestStructSpecSeriesData_SiblingGroup_TS(StructuredMessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_sg'
    filename = ('structured', 'ecb_exr_sg_ts.xml')
    dsd_filename = 'ecb_exr_sg.xml'

    def test_groups(self, msg):
        data = msg.data[0]
        assert len(data.group) == 4
        assert len(data.series) == 4
        g2 = list(data.group.keys())[2]
        assert g2.CURRENCY == 'JPY'
        print(list(data.group.keys()), g2, g2.attrib, sep='\n')
        assert g2.attrib.TITLE == \
            'ECB reference exchange rate, Japanese yen/Euro'
        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        assert isinstance(g_attrib, Mapping)
        assert len(g_attrib) == 1


class TestStructSpecSeriesData_RateGroup_TS(StructuredMessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_rg'
    filename = ('structured', 'ecb_exr_rg_ts.xml')
    dsd_filename = 'ecb_exr_rg.xml'

    def test_groups(self, msg):
        data = msg.data[0]
        assert len(data.group) == 5
        assert len(data.series) == 4
        g2 = list(data.group.keys())[2]
        assert g2.CURRENCY == 'GBP'
        print(list(data.group.keys()), g2, g2.attrib, sep='\n')
        assert g2.attrib.TITLE == \
            'ECB reference exchange rate, U.K. Pound sterling /Euro'
        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        assert isinstance(g_attrib, Mapping)
        assert len(g_attrib) == 5
