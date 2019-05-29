import logging

import pandas as pd
import pandasdmx as sdmx
import pytest


def test_open_file():
    # Can't infer message type for unknown file extension
    with pytest.raises(RuntimeError):
        sdmx.open_file('foo.badsuffix')


def test_request():
    # Constructor
    r = sdmx.Request(log_level=logging.ERROR)

    # Invalid agency name (replaces former test_request.py)
    with pytest.raises(ValueError):
        sdmx.Request('noagency')

    # Regular methods
    r.clear_cache()

    r.timeout = 300
    assert r.timeout == 300


@pytest.mark.remote_data
def test_request_get():
    req = sdmx.Request('ESTAT')
    req.get('datastructure', params={'foo': 'bar'}, dry_run=True)

    # Test Request._make_key_from_dsd()
    req.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
             params={'startPeriod': '2007'})

    with pytest.warns(UserWarning, match='agency argument is redundant'):
        req.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
                 params={'startPeriod': '2007'},
                 agency='ESTAT')

    # Using an unknown endpoint is an exception
    with pytest.raises(ValueError):
        req.get('badendpoint', 'id')

    # TODO test req.get(obj) with all IdentifiableArtefact subclasses
    # TODO test req.get(..., validate=False)


@pytest.mark.remote_data
def test_request_make_series_key():
    req = sdmx.Request('ECB')  # noqa: F841

    # TODO add a test that exercises _make_key_from_series
    # req.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
    #          params={'startPeriod': '2007'})


@pytest.mark.remote_data
def test_request_url():
    # URL can be queried without instantiating Request
    sdmx.Request.url('http://sdw-wsrest.ecb.int/service/datastructure/ECB/'
                     'ECB_EXR1/latest?references=all')


@pytest.mark.remote_data
def test_request_preview_data():
    req = sdmx.Request('ECB')

    # List of keys can be retrieved
    keys = req.preview_data('EXR')
    assert isinstance(keys, list)

    # Count of keys can be determined
    assert len(keys) == 4217

    # A filter can be provided, resulting in fewer keys
    keys = req.preview_data('EXR', {'CURRENCY': 'CAD+CHF+CNY'})
    assert len(keys) == 24

    # Result can be converted to pandas object
    keys_pd = sdmx.to_pandas(keys)
    assert isinstance(keys_pd, pd.DataFrame)
    assert len(keys_pd) == 24
