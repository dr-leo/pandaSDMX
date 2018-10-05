from pathlib import Path
from unittest import TestCase

from pandasdmx import Request
from pandasdmx.writer.data2pandas import Writer

test_data_path = Path(__file__).parent / 'data'


class TestAPI(TestCase):
    def test_base_reader_abstract(self):
        """BaseReader cannot be instantiated."""
        from pandasdmx.reader import BaseReader
        with self.assertRaises(TypeError):
            BaseReader(None)

    def test_null_reader(self):
        """Instantiate the null reader."""
        from pandasdmx.reader.null import Reader
        Reader()


def test_flat():
    from collections import namedtuple

    from pandasdmx.model import DataSet, Message, SeriesObservation

    # Create a bare Message
    msg = Message()

    # Recreate the content from exr-flat.json
    msg.header.dim_at_obs = 'AllDimensions'
    msg.header.id = '62b5f19d-f1c9-495d-8446-a3661ed24753'
    msg.header.prepared = '2012-11-29T08:40:26Z'
    msg.header.sender = 'ECB'

    ds = DataSet()

    # FIXME in exr-flat.json, these are stored in two places:
    #   $.structure.dimensions.dataSet:
    #      FREQ, CURRENCY_DENOM, EXR_TYPE, EXR_SUFFIX
    #   $.structure.dimensions.observation:
    #      CURRENCY, TIME_PERIOD
    #
    # It should be possible to create them programmatically by setting:
    #   msg.structure.dimensions.dataset[0] = Dimension('FREQ'…)
    #   msg.structure.dimensions.observation = …
    GenericObservationKey = namedtuple(
        'GenericObservationKey',
        'FREQ CURRENCY CURRENCY_DENOM EXR_TYPE EXR_SUFFIX TIME_PERIOD',
        )
    key = GenericObservationKey('D', 'NZD', 'EUR', 'SP00', 'A', '2013-01-18')

    # FIXME in exr-flat.json, these are stored at the path:
    #   $.structure.attributes.observation.
    #
    # It should be possible to create them programmatically by setting:
    #   msg.structure.attributes.observation = …
    ObsAttributes = namedtuple('ObsAttributes', 'TITLE OBS_STATUS')
    attrib = ObsAttributes(None, 'A')

    ds.obs.append(SeriesObservation(key, 1.5931, attrib))

    key = key._replace(TIME_PERIOD='2013-01-21')
    ds.obs.append(SeriesObservation(key, 1.5925, attrib))

    key = key._replace(CURRENCY='RUB', TIME_PERIOD='2013-01-18')
    ds.obs.append(SeriesObservation(key, 40.3426, attrib))

    key = key._replace(TIME_PERIOD='2013-01-21')
    ds.obs.append(SeriesObservation(key, 40.3000, attrib))

    msg.data = ds

    # Write to pd.Dataframe
    df1 = Writer(msg).write(msg)

    ref = Request().get(fromfile=test_data_path / 'json' / 'exr-flat.json').msg
    df2 = Writer(ref).write(ref)

    assert (df1 == df2).all()
    # assert False  # Works, but still other changes to be made


def test_bare_series():
    ref = Request().get(fromfile=test_data_path / 'exr' / 'ecb_exr_ng' /
                        'generic' / 'ecb_exr_ng_ts.xml').msg

    for s in ref.data.series:
        print(s)
        for o in s.iter_obs():
            print(o)

    # TODO generate the following series and observations

    # Attrib(DECIMALS='4', UNIT_MEASURE='CHF', UNIT_MULT='0', COLL_METHOD='Average of observations through period', TITLE='ECB reference exchange rate, Swiss franc/Euro')
    # SeriesKey(FREQ='M', CURRENCY='CHF', CURRENCY_DENOM='EUR', EXR_TYPE='SP00', EXR_VAR='E')
    # SeriesObservation(dim='2010-08', value='1.3413', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-09', value='1.3089', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-10', value='1.3452', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))

    # Attrib(DECIMALS='5', UNIT_MEASURE='GBP', UNIT_MULT='0', COLL_METHOD='Average of observations through period', TITLE='ECB reference exchange rate, U.K. Pound sterling /Euro')
    # SeriesKey(FREQ='M', CURRENCY='GBP', CURRENCY_DENOM='EUR', EXR_TYPE='SP00', EXR_VAR='E')
    # SeriesObservation(dim='2010-08', value='0.82363', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-09', value='0.83987', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-10', value='0.87637', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))

    # Attrib(DECIMALS='2', UNIT_MEASURE='JPY', UNIT_MULT='0', COLL_METHOD='Average of observations through period', TITLE='ECB reference exchange rate, Japanese yen/Euro')
    # SeriesKey(FREQ='M', CURRENCY='JPY', CURRENCY_DENOM='EUR', EXR_TYPE='SP00', EXR_VAR='E')
    # SeriesObservation(dim='2010-08', value='110.04', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-09', value='110.26', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-10', value='113.67', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))

    # Attrib(DECIMALS='4', UNIT_MEASURE='USD', UNIT_MULT='0', COLL_METHOD='Average of observations through period', TITLE='ECB reference exchange rate, U.S. dollar/Euro')
    # SeriesKey(FREQ='M', CURRENCY='USD', CURRENCY_DENOM='EUR', EXR_TYPE='SP00', EXR_VAR='E')
    # SeriesObservation(dim='2010-08', value='1.2894', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-09', value='1.3067', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))
    # SeriesObservation(dim='2010-10', value='1.3898', attrib=ObsAttributes(OBS_STATUS='A', CONF_STATUS_OBS='F'))

    assert False
