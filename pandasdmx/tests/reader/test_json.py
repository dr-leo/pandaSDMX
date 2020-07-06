import pytest

import sdmx
from sdmx.tests.data import specimen, test_files


@pytest.mark.parametrize("path", **test_files(format="json"))
def test_json_read(path):
    """Test that the samples from the SDMX-JSON spec can be read."""
    sdmx.read_sdmx(path)


def test_header():
    with specimen("flat.json") as f:
        resp = sdmx.read_sdmx(f)
    assert resp.header.id == "62b5f19d-f1c9-495d-8446-a3661ed24753"
