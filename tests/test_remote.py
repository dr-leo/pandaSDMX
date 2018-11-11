from pathlib import Path

from . import has_requests_cache, requires_requests_cache
import pytest

from pandasdmx.remote import REST


@pytest.fixture(params=['xml', 'json'])
def tmpfile(tmpdir, request):
    """Path to an empty temporary file."""
    path = Path(tmpdir / 'temp.' + request.param)
    path.touch()
    return path


@pytest.mark.skipif(has_requests_cache, reason='test without requests_cache')
def test_without_requests_cache():
    # Passing cache= arguments when requests_cache is not installed triggers a
    # warning
    with pytest.warns(RuntimeWarning):
        REST(cache=dict(cache_name='test'))


@requires_requests_cache
def test_REST_init_cache():
    # Instantiate a REST object with cache
    REST(cache=dict(cache_name='test'))


def test_REST_init_default():
    r = REST()
    assert r.config['timeout'] == 30.1

    r = REST(http_cfg=dict(timeout=10))
    assert r.config['timeout'] == 10
