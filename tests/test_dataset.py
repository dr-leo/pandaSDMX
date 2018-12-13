# encoding: utf-8

'''


@author: Dr. Leo
'''
import pandas as pd
import pandasdmx
from pandasdmx import message, model

from . import MessageTest, test_data_path


class DataMessageTest(MessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_ng' / 'generic'


class TestGenericFlatDataSet(DataMessageTest):
    filename = 'ecb_exr_ng_flat.xml'

    def test_msg_type(self, msg):
        assert isinstance(msg, message.DataMessage)

    def test_header_attributes(self, msg):
        # CHANGED: the internal reference ID of the StructureUsage and the
        #          maintained ID of the DataStructureDefinition it references
        #          are both available
        assert msg.dataflow.id == 'STR1'
        assert msg.structure.id == 'ECB_EXR_NG'
        assert msg.observation_dimension == model.AllDimensions

    def test_generic_obs(self, msg):
        data = msg.data[0]

        # No series
        assert len(data.series) == 0

        # Number of observations
        assert len(data.obs) == 12

        o0 = data.obs[0]

        # REMOVE? What is this measuring?
        # - Not the length of the Observation.key—that is 6.
        # - Something else?
        # assert len(o0) ==  3

        assert isinstance(o0.key, model.Key)
        assert o0.key.FREQ == 'M'
        assert o0.key.CURRENCY == 'CHF'
        assert o0.value == '1.3413'

        # REMOVE: duck typing → test for desired behaviour of attrib instead
        # assert isinstance(o0.attrib, tuple)

        assert o0.attrib.OBS_STATUS == 'A'
        assert o0.attrib.DECIMALS == '4'

    def test_write2pandas(self, msg):
        data_series = pandasdmx.to_pandas(msg.data[0], attributes='',
                                          asframe=False)
        assert isinstance(data_series, pd.Series)


class TestGenericSeriesDataSet(DataMessageTest):
    filename = 'ecb_exr_ng_ts_gf.xml'

    def test_header_attributes(self, msg):
        assert msg.dataflow.id == 'STR1'
        assert msg.structure.id == 'ECB_EXR_NG'
        assert msg.observation_dimension == ['TIME_PERIOD']

    def test_generic_obs(self, msg):
        data = msg.data[0]

        # Number of observations in the dataset
        # CHANGED: obs gives access to all observations in the data set
        assert len(data.obs) == 12

        # Number of series in the dataset
        assert len(data.series) == 4

        # Access to series by index
        s3 = data.series[3]

        # REMOVE: Series is not in the IM
        # assert isinstance(s3, model.Series)

        # Observations in series have .series_key with correct length & values
        assert isinstance(s3[0].series_key, model.Key)
        assert len(s3[0].series_key) == 5
        assert s3[0].series_key.CURRENCY == 'USD'

        # Observations in series have attributes
        assert s3[0].attrib.DECIMALS == '4'

        # Number of observations in the series
        assert len(s3) == 3

        # Series observations can be reversed, and accessed by index
        o0 = list(reversed(s3))[2]

        # REMOVE? see TestGenericFlatDataSet.test_generic_obs
        # assert len(o0) == 3

        # Series observations have expected value
        assert o0.dim == '2010-08'
        assert o0.value == '1.2894'

        # REMOVE: see TestGenericFlatDataSet.test_generic_obs
        # assert isinstance(o0.attrib, tuple)

        assert o0.attrib.OBS_STATUS == 'A'

    def test_pandas(self, msg):
        data = msg.data[0]

        series_keys = list(data.series.keys())

        # Number of series in dataframe
        assert len(series_keys) == 4

        # Convert the observations for one SeriesKey to a pd.Series
        s3_key = series_keys[3]
        s3 = pandasdmx.to_pandas(data.series[s3_key])
        assert isinstance(s3, pd.Series)

        # Test a particular value
        assert s3[0] == 1.2894

        # Length of index
        assert len(s3.index.names) == 6

        # Convert again, with attributes
        pd_data = pandasdmx.to_pandas(data, attributes='osgd')

        # Select one SeriesKey's data out of the DataFrame
        keys, levels = zip(*[(kv.value, kv.id) for kv in s3_key])
        s3 = pd_data.xs(keys, level=levels, drop_level=False)

        # Get the value of the first observation
        assert s3.iloc[0].value == 1.2894

        # Length of index
        assert len(s3.index.names) == 6

        # Number of attributes available
        assert len(set(s3.columns) - {'value'}) == 7

        # Access an attribute of the first value.
        # NB that this uses…
        # 1. the *pandas* attribute access shorthand, NOT DictLike:
        #    "s3.iloc[0]" is a single row of s3, i.e. a pd.Series; and
        #    ".OBS_STATUS" accesses the ps.Series element associated with that
        #    key in the index
        # 2. the AttributeValue.__eq__() comparison operator;
        #    s3.iloc[0].OBS_STATUS is a full AttributeValue, rather than a str.
        assert s3.iloc[0].OBS_STATUS == 'A'
        assert s3.iloc[0].OBS_STATUS.value_for == 'OBS_STATUS'  # consistency!

    def test_pandas_with_freq(self):
        resp = self.resp
        data = resp.data
        pd_series = [s for s in resp.write(
            data, attributes='', reverse_obs=True, asframe=False, fromfreq=True)]
        self.assertEqual(len(pd_series), 4)
        s3 = pd_series[3]
        self.assertIsInstance(s3, pandas.core.series.Series)
        self.assertEqual(s3[2], 1.2894)
        self.assertIsInstance(s3.name, tuple)
        self.assertEqual(len(s3.name), 5)
        # now with attributes
        pd_series = [s for s in resp.write(
            data, attributes='osgd', reverse_obs=True, asframe=False, fromfreq=True)]
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

    def test_write2pandas(self, msg):
        df = pandasdmx.to_pandas(msg, attributes='')

        assert isinstance(df, pd.Series)

        assert df.shape == (12,)
        # with metadata
        df = pandasdmx.to_pandas(msg, attributes='osgd')
        df, mdf = df.iloc[:, 0], df.iloc[:, 1:]
        assert mdf.shape == (12, 7)
        assert mdf.iloc[1].OBS_STATUS == 'A'

    def test_write2pandas_with_freq(self):
        df = self.resp.write(attributes='',
                             reverse_obs=False, fromfreq=True)
        self.assertIsInstance(df, pandas.DataFrame)
        assert df.shape == (3, 4)
        # with metadata
        df, mdf = self.resp.write(attributes='osgd',
                                  reverse_obs=False, fromfreq=True)
        assert mdf.shape == (3, 4)
        assert mdf.iloc[1, 1].OBS_STATUS == 'A'


class TestGenericSeriesDataSet2(DataMessageTest):
    filename = 'ecb_exr_ng_ts.xml'

    def test_header_attributes(self, msg):
        assert msg.dataflow.id == 'STR1'
        assert msg.structure.id == 'ECB_EXR_NG'
        # CHANGED: observation_dimension can be 1-or-more Dimensions; must
        #          compare with an iterable of Dimension or Dimension IDs.
        assert msg.observation_dimension == ['TIME_PERIOD']

    def test_generic_obs(self, msg):
        data = msg.data[0]

        # CHANGED: obs gives access to all observations in the data set
        assert len(data.obs) == 12

        assert len(data.series) == 4
        series_list = list(data.series.values())
        assert len(series_list) == 4
        s3 = series_list[3]

        # REMOVE: Series is not in the IM
        # assert isinstance(s3, model.Series)

        # CHANGED: access SeriesKey from Observations in the series, or keys of
        #          DataSet.series.
        assert isinstance(s3[0].series_key, model.Key)
        assert len(s3[0].series_key) == 5
        assert s3[0].key.CURRENCY == 'USD'
        assert s3[0].attrib.DECIMALS == '4'
        obs_list = list(reversed(s3))
        assert len(obs_list) == 3
        o0 = obs_list[2]

        # REMOVE: see TestGenericFlatDataSet.test_generic_obs
        # assert len(o0) == 3

        assert o0.dim == '2010-08'
        assert o0.value == '1.2894'

        # REMOVE: see TestGenericFlatDataSet.test_generic_obs
        # assert isinstance(o0.attrib, tuple)

        assert o0.attrib.OBS_STATUS == 'A'

    def test_dataframe(self, msg):
        df = pandasdmx.to_pandas(msg.data[0], attributes='',
                                 asframe=True).iloc[::-1]

        assert isinstance(df, pd.Series)

        assert df.shape == (12,)


class TestGenericSeriesData_SiblingGroup_TS(DataMessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_sg' / 'generic'
    filename = 'ecb_exr_sg_ts.xml'

    def test_groups(self, msg):
        data = msg.data[0]

        # CHANGED: groups → group; list() is no longer required
        assert len(data.group) == 4
        assert len(data.series) == 4

        # CHANGED: access GroupKeys from keys of DataSet.group
        g2_key, g2 = list(data.group.items())[2]
        assert g2_key.CURRENCY == 'JPY'
        assert g2[0].attrib.TITLE == ('ECB reference exchange rate, Japanese '
                                      'yen/Euro')

        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        assert len(g_attrib) == 1

        # REMOVE: duck typing → test for desired behaviour of attrib instead
        # assert isinstance(g_attrib, tuple)


class TestGenericSeriesData_RateGroup_TS(DataMessageTest):
    path = test_data_path / 'exr' / 'ecb_exr_rg' / 'generic'
    filename = 'ecb_exr_rg_ts.xml'

    def test_groups(self, msg):
        data = msg.data[0]

        # CHANGED: groups → group; list() is no longer required
        assert len(data.group) == 5
        assert len(data.series) == 4

        # CHANGED: .group is DictLike; retrieve the key and obs separately
        g2_key, g2 = list(data.group.items())[2]
        assert g2_key.CURRENCY == 'GBP'
        assert g2_key.attrib.TITLE == ('ECB reference exchange rate, U.K. '
                                       'Pound sterling /Euro')
        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        assert len(g_attrib) == 5

        # REMOVE: see TestGenericFlatDataSet.test_generic_obs
        # assert isinstance(g_attrib, tuple)

    def test_footer(self):
        f = pandasdmx.open_file(test_data_path / 'estat' / 'footer.xml').footer
        assert f.code == 413
        assert f.severity == 'Infomation'
        assert str(f.text[1]).startswith('http')
