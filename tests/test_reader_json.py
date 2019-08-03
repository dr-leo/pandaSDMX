import pandasdmx as sdmx
import pytest

from . import test_data_path, test_files


@pytest.mark.parametrize('path', **test_files(format='json'))
def test_json_read(path):
    """Test that the samples from the SDMX-JSON spec can be read."""
    sdmx.read_sdmx(path)


def test_header():
    resp = sdmx.read_sdmx(test_data_path / 'json' / 'exr-flat.json')
    assert resp.header.id == '62b5f19d-f1c9-495d-8446-a3661ed24753'
