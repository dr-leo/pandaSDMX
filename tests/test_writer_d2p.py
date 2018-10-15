import pytest

from pandasdmx.writer.data2pandas import Writer

from . import test_data_path


test_data_path = test_data_path / 'exr' / 'ecb_exr_ng' / 'generic'

test_data = list(test_data_path.iterdir())


@pytest.mark.skip
@pytest.mark.parametrize('path', test_data)
def test_read_xml(empty_req, path):
    msg = empty_req.get(fromfile=path).msg

    Writer(msg).write(msg)
