"""Test URL generation by api.Request"""
from pandasdmx.api import Request, Resource
from pandasdmx.source import add_source, sources


def _base_kwargs(resource_type="data", **kwargs):
    result = {"resource_type": resource_type}
    result.update(kwargs)
    return result


def _check_urls(request, expected, params=None):
    params = params or {}
    expected_url = "https://example.org/sdmx/data"
    kwargs = _base_kwargs("data", **params)
    assert request._request_from_args(kwargs).url == expected_url

    expected_url = f"https://example.org/sdmx/actualconstraint/{expected}/latest"
    kwargs = _base_kwargs("actualconstraint", **params)
    assert request._request_from_args(kwargs).url == expected_url


def test_provider_precedence():
    # Create request
    sources.clear()
    add_source(
        {
            "id": "FOO",
            "name": "Demo source",
            "supports": {Resource.actualconstraint: True},
            "url": "https://example.org/sdmx"
        }
    )
    request = Request("FOO")

    # Defaults to request.source.id
    _check_urls(request, "FOO")

    # request.source.api_id overrides
    request.source.api_id = "BAR"
    _check_urls(request, "BAR")

    # provider param overrides
    _check_urls(request, "BAZ", {"provider": "BAZ"})




