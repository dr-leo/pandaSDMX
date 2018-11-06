from pathlib import Path

from pandasdmx import Request
from pandasdmx.model import (
    AttributeValue,
    Header,
    DataAttribute,
    DataSet,
    DataMessage,
    Key,
    Observation,
    )
from pandasdmx.writer.data2pandas import Writer

test_data_path = Path(__file__).parent / 'data'


def test_flat():

    # Create a bare Message
    msg = DataMessage()

    # Recreate the content from exr-flat.json
    header = Header(
        id='62b5f19d-f1c9-495d-8446-a3661ed24753',
        prepared='2012-11-29T08:40:26Z',
        sender='ECB',
        )
    msg.header = header

    ds = DataSet()

    # Create a Key and attributes
    key = Key(FREQ='D', CURRENCY='NZD', CURRENCY_DENOM='EUR', EXR_TYPE='SP00',
              EXR_SUFFIX='A', TIME_PERIOD='2013-01-18')
    obs_status = DataAttribute(id='OBS_STATUS')
    attr = {'OBS_STATUS': AttributeValue(value_for=obs_status, value='A')}

    ds.obs.append(Observation(dimension=key, value=1.5931,
                  attached_attribute=attr))

    key = key.copy(TIME_PERIOD='2013-01-21')
    ds.obs.append(Observation(dimension=key, value=1.5925,
                  attached_attribute=attr))

    key = key.copy(CURRENCY='RUB', TIME_PERIOD='2013-01-18')
    ds.obs.append(Observation(dimension=key, value=40.3426,
                  attached_attribute=attr))

    key = key.copy(TIME_PERIOD='2013-01-21')
    ds.obs.append(Observation(dimension=key, value=40.3000,
                  attached_attribute=attr))

    msg.data.append(ds)

    # COMMENTED: refactoring
    #
    # # Write to pd.Dataframe
    # df1 = Writer(msg).write(msg)
    #
    # ref = Request().get(fromfile=test_data_path / 'json' / 'exr-flat.json')
    # df2 = Writer(ref).write(ref.msg)
    #
    # assert (df1 == df2).all()


def test_bare_series():
    Request().get(fromfile=test_data_path / 'exr' / 'ecb_exr_ng' /
                  'generic' / 'ecb_exr_ng_ts.xml').msg

    # TODO generate the series and observations
