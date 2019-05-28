from pathlib import Path

from . import has_requests_cache
import pytest

from pandasdmx.remote import Session


@pytest.fixture(params=['xml', 'json'])
def tmpfile(tmpdir, request):
    """Path to an empty temporary file."""
    path = Path(tmpdir / 'temp.' + request.param)
    path.touch()
    return path


@pytest.mark.skipif(has_requests_cache, reason='test without requests_cache')
def test_session_without_requests_cache():
    # Passing cache= arguments when requests_cache is not installed triggers a
    # warning
    with pytest.warns(RuntimeWarning):
        Session(cache_name='test')


@pytest.mark.remote_data
def test_session_init_cache(tmpdir):
    # Instantiate a REST object with cache
    cache_name = Path(tmpdir.join('pandasdmx_cache'))
    s = Session(cache_name=str(cache_name), backend='sqlite')

    # Get a resource
    s.get('https://registry.sdmx.org/ws/rest/dataflow')

    # Test for existence of cache file
    assert cache_name.with_suffix('.sqlite').exists()
