from io import StringIO
import logging

import pandas as pd
import pandasdmx as sdmx
import pytest

from . import specimen


def test_read_sdmx(tmp_path):
    # Copy the file to a temporary file with an urecognizable suffix
    target = tmp_path / 'foo.badsuffix'
    with specimen('exr-flat.json', opened=False) as original:
        target.open('w').write(original.read_text())

    # Can't infer message type for unknown file extension
    exc = ("cannot identify SDMX message format from file name 'foo.badsuffix'"
           "; use  format='...'")
    with pytest.raises(RuntimeError, match=exc):
        sdmx.read_sdmx(target)

    # Using the format= kwarg suppresses the error
    sdmx.read_sdmx(target, format='JSON')

    # Format can be inferred from an already-open file without extension
    with specimen('exr-flat.json') as f:
        sdmx.read_sdmx(f)

    # Exception raised when the file contents don't allow to guess the format
    bad_file = StringIO('#! neither XML nor JSON')
    exc = "cannot infer SDMX message format from '#! ne..'"
    with pytest.raises(RuntimeError, match=exc):
        sdmx.read_sdmx(bad_file)



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


def test_request_get_exceptions():
    """Tests of Request.get() that don't require remote data."""
    req = sdmx.Request('ESTAT')

    # Exception is raised on unrecognized arguments
    exc = "unrecognized arguments: {'foo': 'bar'}"
    with pytest.raises(ValueError, match=exc):
        req.get('datastructure', foo='bar')

    with pytest.raises(ValueError, match=exc):
        sdmx.read_url('https://example.com', foo='bar')


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
def test_read_url():
    # URL can be queried without instantiating Request
    sdmx.read_url('http://sdw-wsrest.ecb.int/service/datastructure/ECB/'
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
