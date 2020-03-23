import pandas as pd
import pandas.testing as pdt
import pandasdmx as sdmx
from pandasdmx import message, model

from . import MessageTest
from .data import specimen


class DataMessageTest(MessageTest):
    path = MessageTest.path / 'ECB_EXR'


class TestGenericFlatDataSet(DataMessageTest):
    filename = 'ng-flat.xml'

    def test_msg_type(self, msg):
        assert isinstance(msg, message.DataMessage)

    def test_header_attributes(self, msg):
        # Internal reference of the StructureUsage is available
        assert msg.dataflow.id == 'STR1'

        # Maintained ID of the DataStructureDefinition is available
        assert msg.structure.id == 'ECB_EXR_NG'
        assert msg.observation_dimension == model.AllDimensions

    def test_generic_obs(self, msg):
        data = msg.data[0]

        # No series
        assert len(data.series) == 0

        # Number of observations
        assert len(data.obs) == 12

        o0 = data.obs[0]

        assert isinstance(o0.key, model.Key)
        assert o0.key.FREQ == 'M'
        assert o0.key.CURRENCY == 'CHF'
        assert o0.value == '1.3413'

        assert o0.attrib.OBS_STATUS == 'A'
        assert o0.attrib.DECIMALS == '4'

    def test_to_pandas(self, msg):
        # Single data series is converted to pd.Series
        data_series = sdmx.to_pandas(msg.data[0])
        assert isinstance(data_series, pd.Series)

        # When len(msg.data) is 1, the data series in a single Dataset are
        # unwrapped automatically
        assert len(msg.data) == 1
        data_series2 = sdmx.to_pandas(msg.data)  # NB no '[0]' index
        pdt.assert_series_equal(data_series, data_series2)


class TestGenericSeriesDataSet(DataMessageTest):
    filename = 'ng-ts-gf.xml'

    def test_header_attributes(self, msg):
        assert msg.dataflow.id == 'STR1'
        assert msg.structure.id == 'ECB_EXR_NG'
        assert msg.observation_dimension == 'TIME_PERIOD'

    def test_generic_obs(self, msg):
        data = msg.data[0]

        # Number of observations in the entire dataset
        assert len(data.obs) == 12

        # Number of series in the dataset
        assert len(data.series) == 4

        # Access to series by index
        s3 = data.series[3]

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

        # Series observations have expected value
        assert o0.dim == '2010-08'
        assert o0.value == '1.2894'

        assert o0.attrib.OBS_STATUS == 'A'

    def test_pandas(self, msg):
        data = msg.data[0]

        series_keys = list(data.series.keys())

        # Number of series in dataframe
        assert len(series_keys) == 4

        # Convert the observations for one SeriesKey to a pd.Series
        s3_key = series_keys[3]
        s3 = sdmx.to_pandas(data.series[s3_key])
        assert isinstance(s3, pd.Series)

        # Test a particular value
        assert s3[0] == 1.2894

        # Length of index
        assert len(s3.index.names) == 6

        # Convert again, with attributes
        pd_data = sdmx.to_pandas(data, attributes='osgd')

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

    def test_write2pandas(self, msg):
        df = sdmx.to_pandas(msg, attributes='')

        assert isinstance(df, pd.Series)

        assert df.shape == (12,)

        # with metadata
        df = sdmx.to_pandas(msg, attributes='osgd')
        df, mdf = df.iloc[:, 0], df.iloc[:, 1:]
        assert mdf.shape == (12, 7)
        assert mdf.iloc[1].OBS_STATUS == 'A'


class TestGenericSeriesDataSet2(DataMessageTest):
    filename = 'ng-ts.xml'

    def test_header_attributes(self, msg):
        assert msg.dataflow.id == 'STR1'
        assert msg.structure.id == 'ECB_EXR_NG'

        # Observation dimension is 1 or more Dimensions
        assert msg.observation_dimension == 'TIME_PERIOD'

    def test_generic_obs(self, msg):
        data = msg.data[0]

        assert len(data.obs) == 12

        assert len(data.series) == 4
        series_list = list(data.series.values())
        assert len(series_list) == 4
        s3 = series_list[3]

        # SeriesKey can be accessed by reference from each Observation in the
        # series
        assert isinstance(s3[0].series_key, model.Key)

        assert len(s3[0].series_key) == 5
        assert s3[0].key.CURRENCY == 'USD'
        assert s3[0].attrib.DECIMALS == '4'
        obs_list = list(reversed(s3))
        assert len(obs_list) == 3
        o0 = obs_list[2]

        assert o0.dim == '2010-08'
        assert o0.value == '1.2894'

        assert o0.attrib.OBS_STATUS == 'A'

    def test_dataframe(self, msg):
        df = sdmx.to_pandas(msg.data[0]).iloc[::-1]

        assert isinstance(df, pd.Series)

        assert df.shape == (12,)


class TestGenericSeriesData_SiblingGroup_TS(DataMessageTest):
    filename = 'sg-ts.xml'

    def test_groups(self, msg):
        data = msg.data[0]

        # Data have expected number of groups and series
        assert len(data.group) == 4
        assert len(data.series) == 4

        # GroupKeys can be retrieved from keys of DataSet.group
        g2_key, g2 = list(data.group.items())[2]
        assert g2_key.CURRENCY == 'JPY'
        assert g2[0].attrib.TITLE == ('ECB reference exchange rate, Japanese '
                                      'yen/Euro')

        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        assert len(g_attrib) == 1


class TestGenericSeriesData_RateGroup_TS(DataMessageTest):
    filename = 'rg-ts.xml'

    def test_groups(self, msg):
        data = msg.data[0]

        assert len(data.group) == 5
        assert len(data.series) == 4

        # .group is DictLike; retrieve the key and obs separately
        g2_key, g2 = list(data.group.items())[2]
        assert g2_key.CURRENCY == 'GBP'
        assert g2_key.attrib.TITLE == ('ECB reference exchange rate, U.K. '
                                       'Pound sterling /Euro')
        # Check group attributes of a series
        s = list(data.series)[0]
        g_attrib = s.group_attrib
        assert len(g_attrib) == 5

    def test_footer(self):
        with specimen('footer.xml') as f:
            f = sdmx.read_sdmx(f).footer
        assert f.code == 413
        assert f.severity == 'Infomation'
        assert str(f.text[1]).startswith('http')
