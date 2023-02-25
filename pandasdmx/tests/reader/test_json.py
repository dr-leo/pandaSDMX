import pytest

import pandasdmx
from pandasdmx.tests.data import specimen 
from pandasdmx.tests.data import test_files as _test_files


@pytest.mark.parametrize("path", **_test_files(format="json"))
def test_json_read(path):
    """Test that the samples from the pandasdmx.JSON spec can be read."""
    pandasdmx.read_sdmx(path)


def test_header():
    with specimen("flat.json") as f:
        resp = pandasdmx.read_sdmx(f)
    assert resp.header.id == "62b5f19d-f1c9-495d-8446-a3661ed24753"
