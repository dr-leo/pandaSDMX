# encoding: utf-8

'''


@author: Dr. Leo
'''
import pytest

import pandas

from pandasdmx import model, Request

from . import test_data_path


class TestGenericFlatDataSet:
    @pytest.fixture(scope='class')
    def resp(self):
        return Request().get(fromfile=test_data_path / 'exr' / 'ecb_exr_ng' /
                             'generic' / 'ecb_exr_ng_flat.xml').msg

    def test_msg_type(self, resp):
        assert isinstance(resp, model.DataMessage)

    def test_header_attributes(self, resp):
        # CHANGED: the internal reference ID of the StructureUsage and the
        #          maintained ID of the DataStructureDefinition it references
        #          are both available
        assert resp.dataflow.id == 'STR1'
        assert resp.structure.id == 'ECB_EXR_NG'
        assert resp.observation_dimension == model.AllDimensions

    def test_generic_obs(self, resp):
        data = resp.data[0]

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

    @pytest.mark.xfail(reason='refactoring: writer')
    def test_write2pandas(self, resp):
        data_series = resp.write(attributes='', asframe=False)
        assert isinstance(data_series, pandas.Series)


class TestGenericSeriesDataSet:
    @pytest.fixture(scope='class')
    def resp(self):
        return Request().get(fromfile=test_data_path / 'exr' / 'ecb_exr_ng' /
                             'generic' / 'ecb_exr_ng_ts_gf.xml').msg

    def test_header_attributes(self, resp):
        assert resp.dataflow.id == 'STR1'
        assert resp.structure.id == 'ECB_EXR_NG'
        assert resp.observation_dimension == ['TIME_PERIOD']

    def test_generic_obs(self, resp):
        data = resp.data[0]

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

    @pytest.mark.xfail(reason='refactoring: writer')
    def test_pandas(self, resp):
        data = resp.data[0]
        pd_series = [s.iloc[::-1] for s in resp.write(
                     data, attributes='', asframe=False)]
        assert len(pd_series) == 4
        s3 = pd_series[3]
        assert isinstance(s3, pandas.core.series.Series)
        assert s3[2] == 1.2894
        assert isinstance(s3.name, tuple)
        assert len(s3.name) == 5
        # now with attributes
        pd_series = [s.iloc[::-1] for s in resp.write(
                     data, attributes='osgd', asframe=False)]
        assert len(pd_series) == 4
        assert isinstance(pd_series[0], tuple)  # contains 2 series
        assert len(pd_series[0]) == 2
        s3, a3 = pd_series[3]
        assert isinstance(s3, pandas.core.series.Series)
        assert isinstance(a3, pandas.core.series.Series)
        assert s3[2] == 1.2894
        assert isinstance(s3.name, tuple)
        assert len(s3.name) == 5
        assert len(a3) == 3
        # access an attribute of the first value
        assert a3[0].OBS_STATUS == 'A'

    @pytest.mark.xfail(reason='refactoring: writer')
    def test_write2pandas(self, resp):
        df = resp.write(attributes='')
        assert isinstance(df, pandas.DataFrame)
        assert df.shape == (3, 4)
        # with metadata
        df, mdf = resp.write(attributes='osgd')
        assert mdf.shape == (3, 4)
        assert mdf.iloc[1, 1].OBS_STATUS == 'A'

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


class TestGenericSeriesDataSet2:
    @pytest.fixture(scope='class')
    def resp(self):
        return Request().get(fromfile=test_data_path / 'exr' / 'ecb_exr_ng' /
                             'generic' / 'ecb_exr_ng_ts.xml').msg

    def test_header_attributes(self, resp):
        assert resp.dataflow.id == 'STR1'
        assert resp.structure.id == 'ECB_EXR_NG'
        # CHANGED: observation_dimension can be 1-or-more Dimensions; must
        #          compare with an iterable of Dimension or Dimension IDs.
        assert resp.observation_dimension == ['TIME_PERIOD']

    def test_generic_obs(self, resp):
        data = resp.data[0]

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

    @pytest.mark.xfail(reason='refactoring: writer')
    def test_dataframe(self, resp):
        data = resp.data[0]
        df = resp.write(data, attributes='', asframe=True).iloc[::-1]
        assert isinstance(df, pandas.DataFrame)
        assert df.shape, (3 == 4)


class TestGenericSeriesData_SiblingGroup_TS:
    @pytest.fixture(scope='class')
    def resp(self):
        return Request().get(fromfile=test_data_path / 'exr' / 'ecb_exr_sg' /
                             'generic' / 'ecb_exr_sg_ts.xml').msg

    def test_groups(self, resp):
        data = resp.data[0]

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


class TestGenericSeriesData_RateGroup_TS:
    @pytest.fixture(scope='class')
    def resp(self):
        return Request().get(fromfile=test_data_path / 'exr' / 'ecb_exr_rg' /
                             'generic' / 'ecb_exr_rg_ts.xml').msg

    def test_groups(self, resp):
        data = resp.data[0]

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
        f = Request().get(fromfile=test_data_path / 'estat' / 'footer.xml',
                          get_footer_url=None).footer
        assert f.code == 413
        assert f.severity == 'Infomation'
        assert str(f.text[1]).startswith('http')
