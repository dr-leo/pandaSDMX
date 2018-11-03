# encoding: utf-8

'''


@author: Dr. Leo
'''
import unittest
import pytest

import pandas

from pandasdmx import model, Request

from . import test_data_path


pytestmark = pytest.mark.skip('refactoring')


class TestGenericFlatDataSet(unittest.TestCase):
    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = test_data_path.joinpath('exr', 'ecb_exr_ng', 'generic',
                                           'ecb_exr_ng_flat.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_msg_type(self):
        self.assertIsInstance(self.resp.msg, model.DataMessage)

    def test_header_attributes(self):
        self.assertEqual(self.resp.header.structured_by, 'STR1')
        self.assertEqual(self.resp.header.observation_dimension,
                         model.AllDimensions)

    def test_generic_obs(self):
        data = self.resp.data[0]
        # REMOVE: series are not in the data model
        # # empty series list
        # self.assertEqual(len(list(data.series)), 0)
        obs_list = data.obs
        self.assertEqual(len(obs_list), 12)
        o0 = obs_list[0]
        # REMOVE? What is this measuring?
        # - Not the length of the Observation.key—that is 6.
        # - Something else?
        # self.assertEqual(len(o0), 3)
        self.assertIsInstance(o0.key, model.Key)
        self.assertEqual(o0.key.FREQ, 'M')
        self.assertEqual(o0.key.CURRENCY, 'CHF')
        self.assertEqual(o0.value, '1.3413')
        # REMOVE: duck typing → test for desired behaviour of attrib instead
        # self.assertIsInstance(o0.attrib, tuple)
        print(o0.attrib)
        print('foo')
        print(o0.attrib.OBS_STATUS)
        print('bar')
        assert o0.attrib.OBS_STATUS == 'A'
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')
        self.assertEqual(o0.attrib.DECIMALS, '4')

    def test_write2pandas(self):
        data_series = self.resp.write(attributes='', asframe=False)
        self.assertIsInstance(data_series, pandas.Series)


class TestGenericSeriesDataSet(unittest.TestCase):

    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = test_data_path.joinpath('exr', 'ecb_exr_ng', 'generic',
                                           'ecb_exr_ng_ts_gf.xml')
        self.resp = self.estat.data(fromfile=filepath)

    def test_header_attributes(self):
        self.assertEqual(self.resp.header.structured_by, 'STR1')
        self.assertEqual(self.resp.header.dim_at_obs, 'TIME_PERIOD')

    def test_generic_obs(self):
        data = self.resp.data[0]
        # empty obs iterator
        self.assertEqual(len(data.obs), 0)
        series_list = list(data.series)
        self.assertEqual(len(series_list), 4)
        s3 = series_list[3]
        self.assertIsInstance(s3, model.Series)
        self.assertIsInstance(s3.key, model.Key)
        self.assertEqual(len(s3.key), 5)
        self.assertEqual(s3.key.CURRENCY, 'USD')
        self.assertEqual(s3.attrib.DECIMALS, '4')
        obs_list = list(reversed(s3.obs))
        self.assertEqual(len(obs_list), 3)
        o0 = obs_list[2]
        # REMOVE? See line 46.
        # self.assertEqual(len(o0), 3)
        self.assertEqual(o0.dim, '2010-08')
        self.assertEqual(o0.value, '1.2894')
        # REMOVE: see line 54.
        # self.assertIsInstance(o0.attrib, tuple)
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')

    def test_pandas(self):
        resp = self.resp
        data = resp.data[0]
        pd_series = [s.iloc[::-1] for s in resp.write(
                     data, attributes='', asframe=False)]
        self.assertEqual(len(pd_series), 4)
        s3 = pd_series[3]
        self.assertIsInstance(s3, pandas.core.series.Series)
        self.assertEqual(s3[2], 1.2894)
        self.assertIsInstance(s3.name, tuple)
        self.assertEqual(len(s3.name), 5)
        # now with attributes
        pd_series = [s.iloc[::-1] for s in resp.write(
                     data, attributes='osgd', asframe=False)]
        self.assertEqual(len(pd_series), 4)
        self.assertIsInstance(pd_series[0], tuple)  # contains 2 series
        self.assertEqual(len(pd_series[0]), 2)
        s3, a3 = pd_series[3]
        self.assertIsInstance(s3, pandas.core.series.Series)
        self.assertIsInstance(a3, pandas.core.series.Series)
        self.assertEqual(s3[2], 1.2894)
        self.assertIsInstance(s3.name, tuple)
        self.assertEqual(len(s3.name), 5)
        self.assertEqual(len(a3), 3)
        # access an attribute of the first value
        self.assertEqual(a3[0].OBS_STATUS, 'A')

    def test_write2pandas(self):
        df = self.resp.write(attributes='')
        self.assertIsInstance(df, pandas.DataFrame)
        assert df.shape == (3, 4)
        # with metadata
        df, mdf = self.resp.write(attributes='osgd')
        assert mdf.shape == (3, 4)
        assert mdf.iloc[1, 1].OBS_STATUS == 'A'


class TestGenericSeriesDataSet2(unittest.TestCase):

    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = test_data_path.joinpath('exr', 'ecb_exr_ng', 'generic',
                                           'ecb_exr_ng_ts.xml')
        self.resp = self.estat.data(fromfile=filepath)

    def test_header_attributes(self):
        self.assertEqual(self.resp.header.structured_by, 'STR1')
        self.assertEqual(self.resp.header.dim_at_obs, 'TIME_PERIOD')

    def test_generic_obs(self):
        data = self.resp.data[0]
        # empty obs iterator
        self.assertEqual(len(data.obs), 0)
        series_list = list(data.series)
        self.assertEqual(len(series_list), 4)
        s3 = series_list[3]
        self.assertIsInstance(s3, model.Series)
        self.assertIsInstance(s3.key, model.Key)
        self.assertEqual(len(s3.key), 5)
        self.assertEqual(s3.key.CURRENCY, 'USD')
        self.assertEqual(s3.attrib.DECIMALS, '4')
        obs_list = list(reversed(s3.obs))
        self.assertEqual(len(obs_list), 3)
        o0 = obs_list[2]
        # REMOVE: see line 54.
        # self.assertEqual(len(o0), 3)
        self.assertEqual(o0.dim, '2010-08')
        self.assertEqual(o0.value, '1.2894')
        # REMOVE: see line 54.
        # self.assertIsInstance(o0.attrib, tuple)
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')

    def test_dataframe(self):
        data = self.resp.data[0]
        df = self.resp.write(data, attributes='', asframe=True).iloc[::-1]
        self.assertIsInstance(df, pandas.DataFrame)
        self.assertEqual(df.shape, (3, 4))


class TestGenericSeriesData_SiblingGroup_TS(unittest.TestCase):

    def setUp(self):
        self.estat = Request()
        filepath = test_data_path.joinpath('exr', 'ecb_exr_sg', 'generic',
                                           'ecb_exr_sg_ts.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_groups(self):
        data = self.resp.data[0]
        self.assertEqual(len(list(data.groups)), 4)
        self.assertEqual(len(list(data.series)), 4)
        g2 = list(data.groups)[2]
        self.assertEqual(g2.key.CURRENCY, 'JPY')
        self.assertEqual(
            g2.attrib.TITLE, 'ECB reference exchange rate, Japanese yen/Euro')
        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        self.assertEqual(len(g_attrib), 1)
        # REMOVE: duck typing → test for desired behaviour of attrib instead
        # self.assertIsInstance(g_attrib, tuple)


class TestGenericSeriesData_RateGroup_TS(unittest.TestCase):

    def setUp(self):
        self.estat = Request()
        filepath = test_data_path.joinpath('exr', 'ecb_exr_rg', 'generic',
                                           'ecb_exr_rg_ts.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_groups(self):
        data = self.resp.data[0]
        self.assertEqual(len(list(data.groups)), 5)
        self.assertEqual(len(list(data.series)), 4)
        g2 = list(data.groups)[2]
        self.assertEqual(g2.key.CURRENCY, 'GBP')
        self.assertEqual(
            g2.attrib.TITLE,
            'ECB reference exchange rate, U.K. Pound sterling /Euro')
        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        self.assertEqual(len(g_attrib), 5)
        # REMOVE: duck typing → test for desired behaviour of attrib instead
        # self.assertIsInstance(g_attrib, tuple)

    def test_footer(self):
        filepath = test_data_path / 'estat' / 'footer.xml'
        resp = self.estat.get(
            fromfile=filepath, get_footer_url=None)
        f = resp.footer
        assert f.code == 413
        assert f.severity == 'Infomation'
        assert str(f.text[1]).startswith('http')
