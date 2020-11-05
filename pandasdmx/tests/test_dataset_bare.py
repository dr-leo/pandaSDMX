import pandasdmx
from pandasdmx import  model
from pandasdmx.message import DataMessage, Header
from pandasdmx.model import AttributeValue, DataAttribute, DataSet, Key, Observation

from . import assert_pd_equal
from .data import specimen


def test_flat():
    """
    Display flat flat flat dataframe

    Args:
    """
    # Create a bare Message
    msg = DataMessage()

    # Recreate the content from exr-flat.json
    header = Header(
        id="62b5f19d-f1c9-495d-8446-a3661ed24753",
        prepared="2012-11-29T08:40:26Z",
        sender=model.Agency(id="ECB"),
    )
    msg.header = header

    ds = DataSet()

    # Create a Key and attributes
    key = Key(
        FREQ="D",
        CURRENCY="NZD",
        CURRENCY_DENOM="EUR",
        EXR_TYPE="SP00",
        EXR_SUFFIX="A",
        TIME_PERIOD="2013-01-18",
    )
    obs_status = DataAttribute(id="OBS_STATUS")
    attr = {"OBS_STATUS": AttributeValue(value_for=obs_status, value="A")}

    ds.obs.append(Observation(dimension=key, value=1.5931, attached_attribute=attr))

    key = key.copy(TIME_PERIOD="2013-01-21")
    ds.obs.append(Observation(dimension=key, value=1.5925, attached_attribute=attr))

    key = key.copy(CURRENCY="RUB", TIME_PERIOD="2013-01-18")
    ds.obs.append(Observation(dimension=key, value=40.3426, attached_attribute=attr))

    key = key.copy(TIME_PERIOD="2013-01-21")
    ds.obs.append(Observation(dimension=key, value=40.3000, attached_attribute=attr))

    msg.data.append(ds)

    # Write to pd.Dataframe
    df1 = pandasdmx.to_pandas(msg)

    with specimen("flat.json") as f:
        ref = pandasdmx.read_sdmx(f)
    df2 = pandasdmx.to_pandas(ref)

    assert_pd_equal(df1, df2)


def test_bare_series():
    """
    Read series from the series

    Args:
    """
    with specimen("ng-ts.xml") as f:
        pandasdmx.read_sdmx(f)

    # TODO generate the series and observations
