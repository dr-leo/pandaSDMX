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

    # Invalid source name raise an exception
    with pytest.raises(ValueError):
        sdmx.Request('noagency')

    # Regular methods
    r.clear_cache()

    r.timeout = 300
    assert r.timeout == 300

    # dir() includes convenience methods for resource endpoints
    expected = {'cache', 'clear_cache', 'get', 'preview_data', 'series_keys',
                'session', 'source', 'timeout'}
    expected |= set(ep.name for ep in sdmx.Resource)
    assert set(filter(lambda s: not s.startswith('_'), dir(r))) == expected


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
