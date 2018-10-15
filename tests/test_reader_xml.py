import pytest
from pytest import raises

from pandasdmx.reader.sdmxml import get_message_class

from . import test_data_path


# List all XML files in the 'generic' subdirectories
test_data = []
for part in 'ng', 'rg', 'sg':
    path = test_data_path / 'exr' / 'ecb_exr_{}'.format(part) / 'generic'
    test_data.extend(path.iterdir())


# List structure files
test_structure = [
    test_data_path / 'common' / 'common.xml',
    test_data_path / 'estat' / 'apro_dsd.xml'
    ]


def test_get_message_class():
    with raises(ValueError):
        get_message_class('foo')


# Read example data files
@pytest.mark.skip('working; skip for performance')
@pytest.mark.parametrize('path', test_data)
def test_read_xml(empty_req, path):
    empty_req.get(fromfile=path).msg


# Read example structure files
@pytest.mark.parametrize('path', test_structure)
def test_read_xml_structure(empty_req, path):
    empty_req.get(fromfile=path).msg
