from . import has_requests_cache, requires_requests_cache
import pytest

from pandasdmx.remote import REST


@pytest.mark.skipif(has_requests_cache, reason='test without requests_cache')
def test_without_requests_cache():
    with pytest.warns(RuntimeWarning):
        REST(cache=dict(cache_name='test'))


@requires_requests_cache
def test_REST_init_cache():
    # Instantiate a REST object with cache
    REST(cache=dict(cache_name='test'))
