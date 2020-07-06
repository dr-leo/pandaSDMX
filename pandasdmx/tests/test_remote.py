import pytest

from sdmx.remote import Session

from . import has_requests_cache


@pytest.mark.skipif(has_requests_cache, reason="test without requests_cache")
def test_session_without_requests_cache():  # pragma: no cover
    # Passing cache= arguments when requests_cache is not installed triggers a
    # warning
    with pytest.warns(RuntimeWarning):
        Session(cache_name="test")


@pytest.mark.network
def test_session_init_cache(tmp_path):
    # Instantiate a REST object with cache
    cache_name = tmp_path / "pandasdmx_cache"
    s = Session(cache_name=str(cache_name), backend="sqlite")

    # Get a resource
    s.get("https://registry.sdmx.org/ws/rest/dataflow")

    # Test for existence of cache file
    assert cache_name.with_suffix(".sqlite").exists()
