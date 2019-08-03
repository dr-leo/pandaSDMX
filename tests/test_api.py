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
def test_request_get_args():
    req = sdmx.Request('ESTAT')

    # Request._make_key accepts '+'-separated values
    args = dict(resource_id='une_rt_a', key={'GEO': 'EL+ES+IE'},
                params={'startPeriod': '2007'}, dry_run=True, use_cache=True)
    # Store the URL
    url = req.data(**args).url

    # Using an iterable of key values gives the same URL
    args['key'] = {'GEO': ['EL', 'ES', 'IE']}
    assert req.data(**args).url == url

    # Using a direct string for a key gives the same URL
    args['key'] = '....EL+ES+IE'  # No specified values for first 4 dimensions
    assert req.data(**args).url == url

    # Giving 'provider' is redundant for a data request, causes a warning
    with pytest.warns(UserWarning, match="'provider' argument is redundant"):
        req.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
                 params={'startPeriod': '2007'},
                 provider='ESTAT')

    # Using an unknown endpoint is an exception
    with pytest.raises(ValueError):
        req.get('badendpoint', 'id')

    # TODO test req.get(obj) with IdentifiableArtefact subclasses


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
    assert len(keys) == 4291

    # A filter can be provided, resulting in fewer keys
    keys = req.preview_data('EXR', {'CURRENCY': 'CAD+CHF+CNY'})
    assert len(keys) == 24

    # Result can be converted to pandas object
    keys_pd = sdmx.to_pandas(keys)
    assert isinstance(keys_pd, pd.DataFrame)
    assert len(keys_pd) == 24
