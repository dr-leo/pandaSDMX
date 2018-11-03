import warnings

import pytest

from . import test_data_path


warnings.filterwarnings('error')


# List all XML files in the 'generic' subdirectories
test_data = []
for part in 'ng', 'rg', 'sg':
    path = test_data_path / 'exr' / 'ecb_exr_{}'.format(part) / 'generic'
    test_data.extend(path.iterdir())


# List structure files
test_structure = [test_data_path.joinpath(*parts) for parts in [
    ('common', 'common.xml'),
    ('estat', 'apro_dsd.xml'),
    ('insee', 'insee-bug-data-namedtuple-datastructure.xml'),
    ('insee', 'insee-dataflow.xml'),
    ('insee', 'insee-IPI-2010-A21-datastructure.xml'),
    ]]


# Read example data files
@pytest.mark.parametrize('path', test_data)
def test_read_xml(empty_req, path):
    empty_req.get(fromfile=path).msg


# Read example structure files
@pytest.mark.parametrize('path', test_structure)
def test_read_xml_structure(empty_req, path):
    print(path)
    empty_req.get(fromfile=path).msg
