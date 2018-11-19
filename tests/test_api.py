import logging

from pandasdmx import Request
import pytest


def test_request():
    # Constructor
    r = Request(log_level=logging.ERROR)

    # Invalid agency name (replaces former test_request.py)
    with pytest.raises(ValueError):
        Request('noagency')

    # Regular methods
    r.clear_cache()

    r.timeout = 300
    assert r.timeout == 300


@pytest.mark.remote_data
def test_request_get():
    # TODO test all arguments
    req = Request('ESTAT')
    req.get('datastructure', params={'foo': 'bar'}, dry_run=True)

    # Test Request._make_key_from_dsd()
    req.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
             params={'startPeriod': '2007'})


@pytest.mark.remote_data
def test_request_make_series_key():
    req = Request('ECB')

    # TODO add a test that exercises _make_key_from_series
    # req.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
    #          params={'startPeriod': '2007'})
