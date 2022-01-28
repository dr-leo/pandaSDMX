import json
import logging
from io import BytesIO
import pandas as pd
import pytest
import pandasdmx

from .data import specimen


def test_read_sdmx(tmp_path):
    # Copy the file to a temporary file with an urecognizable suffix
    target = tmp_path / "foo.badsuffix"
    with specimen("flat.json", opened=False) as original:
        target.open("w").write(original.read_text())

    # With unknown file extension, read_sdmx() peeks at the file content
    pandasdmx.read_sdmx(target)

    # Format can be inferred from an already-open file without extension
    with specimen("flat.json") as f:
        pandasdmx.read_sdmx(f)

    # Exception raised when the file contents don't allow to guess the format
    bad_file = BytesIO(b"#! neither XML nor JSON")
    exc = (
        "cannot infer SDMX message format from path None, format={}, or content "
        "'#! ne..'"
    )
    with pytest.raises(RuntimeError, match=exc.format("None")):
        pandasdmx.read_sdmx(bad_file)

    # Using the format= argument forces a certain reader to be used
    # Create new open file:
    bad_file = BytesIO(b"#! neither XML nor JSON")
    with pytest.raises(json.JSONDecodeError):
        pandasdmx.read_sdmx(bad_file, format="JSON")


def test_request():
    # Constructor
    r = pandasdmx.Request(log_level=logging.ERROR)

    # Invalid source name raise an exception
    with pytest.raises(ValueError):
        pandasdmx.Request("noagency")

    # Regular methods
    r.clear_cache()

    r.timeout = 300
    assert r.timeout == 300


def test_request_get_exceptions():
    """Tests of Request.get() that don't require remote data."""
    req = pandasdmx.Request("ESTAT")

    # Exception is raised on unrecognized arguments
    exc = "unrecognized arguments: {'foo': 'bar'}"
    with pytest.raises(ValueError, match=exc):
        req.get("datastructure", foo="bar")

    with pytest.raises(ValueError, match=exc):
        pandasdmx.read_url("https://example.com", foo="bar")


@pytest.mark.network
def test_request_get_args():
    req = pandasdmx.Request("ESTAT")

    # Request._make_key accepts '+'-separated values
    args = dict(
        resource_id="une_rt_a",
        key={"GEO": "EL+ES+IE"},
        params={"startPeriod": "2007"},
        dry_run=True,
        use_cache=True,
    )
    # Store the URL
    url = req.data(**args).url

    # Using an iterable of key values gives the same URL
    args["key"] = {"GEO": ["EL", "ES", "IE"]}
    assert req.data(**args).url == url

    # Using a direct string for a key gives the same URL
    args["key"] = "....EL+ES+IE"  # No specified values for first 4 dimensions
    assert req.data(**args).url == url

    # Giving 'provider' is redundant for a data request, causes a warning
    with pytest.warns(UserWarning, match="'provider' argument is redundant"):
        req.data(
            "une_rt_a",
            key={"GEO": "EL+ES+IE"},
            params={"startPeriod": "2007"},
            provider="ESTAT",
        )

    # Using an unknown endpoint is an exception
    with pytest.raises(ValueError):
        req.get("badendpoint", "id")

    # TODO test req.get(obj) with IdentifiableArtefact subclasses


@pytest.mark.network
def test_read_url():
    # URL can be queried without instantiating Request
    pandasdmx.read_url(
        "https://sdw-wsrest.ecb.europa.eu/service/datastructure/ECB/"
        "ECB_EXR1/latest?references=all"
    )


@pytest.mark.network
def test_request_preview_data():
    req = pandasdmx.Request("ECB")

    # List of keys can be retrieved
    keys = req.preview_data("EXR")
    assert isinstance(keys, list)

    # Count of keys can be determined
    assert len(keys) > 1000

    # A filter can be provided, resulting in fewer keys
    keys = req.preview_data("EXR", {"CURRENCY": "CAD+CHF+CNY"})
    assert len(keys) == 24

    # Result can be converted to pandas object
    keys_pd = pandasdmx.to_pandas(keys)
    assert isinstance(keys_pd, pd.DataFrame)
    assert len(keys_pd) == 24
