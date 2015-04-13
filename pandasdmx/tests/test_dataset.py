# encoding: utf-8

'''


@author: Dr. Leo
'''
import unittest
import pandasdmx
from pandasdmx import model, Request
import pandas
import os.path

pkg_path = pandasdmx.tests.__path__[0]


class TestGenericFlatDataSet(unittest.TestCase):

    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(
            pkg_path, 'data/exr/ecb_exr_ng/generic/ecb_exr_ng_flat.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_msg_type(self):
        self.assertIsInstance(self.resp.msg, model.GenericDataMessage)

    def test_header_attributes(self):
        self.assertEqual(self.resp.msg.header.structured_by, 'STR1')
        self.assertEqual(self.resp.msg.header.dim_at_obs, 'AllDimensions')

    def test_dataset_cls(self):
        self.assertIsInstance(self.resp.msg.data, model.GenericDataSet)
        self.assertEqual(self.resp.msg.data.dim_at_obs, 'AllDimensions')

    def test_generic_obs(self):
        data = self.resp.msg.data
        # empty series list
        self.assertEqual(len(list(data.series)), 0)
        obs_list = list(data.obs())
        self.assertEqual(len(obs_list), 12)
        o0 = obs_list[0]
        self.assertEqual(len(o0), 3)
        self.assertIsInstance(o0.key, tuple)  # obs_key
        self.assertEqual(o0.key.FREQ, 'M')
        self.assertEqual(o0.key.CURRENCY, 'CHF')
        self.assertEqual(o0.value, '1.3413')
        self.assertIsInstance(o0.attrib, dict)
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')
        self.assertEqual(o0.attrib.DECIMALS, '4')

    def test_write2pandas(self):
        pd_series = self.resp.write(attributes='',
                                    asframe=False, reverse_obs=False)
        self.assertIsInstance(pd_series, pandas.Series)


class TestGenericSeriesDataSet(unittest.TestCase):

    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(
            pkg_path, 'data/exr/ecb_exr_ng/generic/ecb_exr_ng_ts_gf.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_header_attributes(self):
        self.assertEqual(self.resp.msg.header.structured_by, 'STR1')
        self.assertEqual(self.resp.msg.header.dim_at_obs, 'TIME_PERIOD')

    def test_dataset_cls(self):
        self.assertIsInstance(self.resp.msg.data, model.GenericDataSet)

    def test_generic_obs(self):
        data = self.resp.msg.data
        # empty obs iterator
        self.assertEqual(len(list(data.obs())), 0)
        series_list = list(data.series)
        self.assertEqual(len(series_list), 4)
        s3 = series_list[3]
        self.assertIsInstance(s3, model.Series)
        self.assertIsInstance(s3.key, tuple)
        self.assertEqual(len(s3.key), 5)
        self.assertEqual(s3.key.CURRENCY, 'USD')
        self.assertEqual(s3.attrib.DECIMALS, '4')
        obs_list = list(s3.obs(reverse_obs=True))
        self.assertEqual(len(obs_list), 3)
        o0 = obs_list[2]
        self.assertEqual(len(o0), 3)
        self.assertEqual(o0.dim, '2010-08')
        self.assertEqual(o0.value, '1.2894')
        self.assertIsInstance(o0.attrib, dict)
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')

    def test_pandas(self):
        resp = self.resp
        data = resp.msg.data
        pd_series = [s for s in resp.write(
            data, attributes='', reverse_obs=True, asframe=False)]
        self.assertEqual(len(pd_series), 4)
        s3 = pd_series[3]
        self.assertIsInstance(s3, pandas.core.series.Series)
        self.assertEqual(s3[2], 1.2894)
        self.assertIsInstance(s3.name, tuple)
        self.assertEqual(len(s3.name), 5)
        # now with attributes
        pd_series = [s for s in resp.write(
            data, attributes='osgd', reverse_obs=True, asframe=False)]
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


class TestGenericSeriesDataSet2(unittest.TestCase):

    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(
            pkg_path, 'data/exr/ecb_exr_ng/generic/ecb_exr_ng_ts.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_header_attributes(self):
        self.assertEqual(self.resp.msg.header.structured_by, 'STR1')
        self.assertEqual(self.resp.msg.header.dim_at_obs, 'TIME_PERIOD')

    def test_dataset_cls(self):
        self.assertIsInstance(self.resp.msg.data, model.GenericDataSet)

    def test_generic_obs(self):
        data = self.resp.msg.data
        # empty obs iterator
        self.assertEqual(len(list(data.obs())), 0)
        series_list = list(data.series)
        self.assertEqual(len(series_list), 4)
        s3 = series_list[3]
        self.assertIsInstance(s3, model.Series)
        self.assertIsInstance(s3.key, tuple)
        self.assertEqual(len(s3.key), 5)
        self.assertEqual(s3.key.CURRENCY, 'USD')
        self.assertEqual(s3.attrib.DECIMALS, '4')
        obs_list = list(s3.obs(reverse_obs=True))
        self.assertEqual(len(obs_list), 3)
        o0 = obs_list[2]
        self.assertEqual(len(o0), 3)
        self.assertEqual(o0.dim, '2010-08')
        self.assertEqual(o0.value, '1.2894')
        self.assertIsInstance(o0.attrib, dict)
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')

    def test_dataframe(self):
        data = self.resp.msg.data
        df = self.resp.write(
            data, attributes='', asframe=True, reverse_obs=True)
        self.assertIsInstance(df, pandas.core.frame.DataFrame)
        self.assertEqual(df.shape, (3, 4))


class TestGenericSeriesData_SiblingGroup_TS(unittest.TestCase):

    def setUp(self):
        self.estat = Request()
        filepath = os.path.join(
            pkg_path, 'data/exr/ecb_exr_sg/generic/ecb_exr_sg_ts.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_groups(self):
        data = self.resp.msg.data
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
        self.assertIsInstance(g_attrib, dict)
        self.assertEqual(len(g_attrib), 1)


class TestGenericSeriesData_RateGroup_TS(unittest.TestCase):

    def setUp(self):
        self.estat = Request()
        filepath = os.path.join(
            pkg_path, 'data/exr/ecb_exr_rg/generic/ecb_exr_rg_ts.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_groups(self):
        data = self.resp.msg.data
        self.assertEqual(len(list(data.groups)), 5)
        self.assertEqual(len(list(data.series)), 4)
        g2 = list(data.groups)[2]
        self.assertEqual(g2.key.CURRENCY, 'GBP')
        self.assertEqual(
            g2.attrib.TITLE, 'ECB reference exchange rate, U.K. Pound sterling /Euro')
        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        self.assertEqual(len(g_attrib), 5)
        self.assertIsInstance(g_attrib, dict)
        self.assertEqual(len(g_attrib), 5)


if __name__ == "__main__":
    import nose
    nose.main()
