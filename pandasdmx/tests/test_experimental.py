"""Tests for experimental code using pandas objects for internal storage.

See sdmx.experimental for more information.
"""
import pytest

from sdmx.experimental import DataSet as PandasDataSet
from sdmx.model import AttributeValue, DataAttribute, DataSet, Key, Observation


# Run the tests on both the standard DataSet class, and the experimental,
# PandasDataSet version
@pytest.mark.parametrize(
    "DataSetType",
    [DataSet, pytest.param(PandasDataSet, marks=pytest.mark.experimental)],
)
def test_add_obs(DataSetType):
    # Create a Key and Attributes
    key = Key(CURRENCY="NZD", CURRENCY_DENOM="EUR", TIME_PERIOD="2018-01-01")
    obs_status = DataAttribute(id="OBS_STATUS")
    attr = {"OBS_STATUS": AttributeValue(value_for=obs_status, value="A")}

    obs = []
    for day, value in enumerate([5, 6, 7]):
        key = key.copy(TIME_PERIOD="2018-01-{:02d}".format(day))
        obs.append(Observation(dimension=key, value=value, attached_attribute=attr))

    ds = DataSetType()
    ds.add_obs(obs)

    # PandasDataSet does not store Observation objects internally, but should
    # emit them when the .obs property is accessed
    assert all(a == b for a, b in zip(ds.obs, obs))
