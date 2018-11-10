import json
import os

import pytest

from pandasdmx.api import Request

from . import test_data_path, test_files


@pytest.mark.parametrize('path', test_files(format='json'))
def test_json_read(req, path):
    """Test that the samples from the SDMX-JSON spec can be read."""
    req.get(fromfile=path).msg


def test_header(req):
    resp = req.get(fromfile=test_data_path / 'json' / 'exr-flat.json')
    assert resp.header.id == '62b5f19d-f1c9-495d-8446-a3661ed24753'


# TODO store the source in the Response
@pytest.mark.skip('DISABLED temporarily: relies on removed Message._reader')
def test_write_source(self):
    """Test the write_source() method."""
    req = Request()
    for name in sample_data.keys():  # Should use test_files
        orig_fn = self._filepath(name)
        temp_fn = self._filepath(name + '-write-source')

        # Read the message
        resp = req.get(fromfile=orig_fn)

        # Write to a temporary JSON file
        resp.write_source(temp_fn)

        # Read the two files and compare JSON (ignores ordering)
        with open(orig_fn) as orig, open(temp_fn) as temp:
            assert json.load(orig) == json.load(temp)

        # Delete the temporary file
        os.remove(temp_fn)
