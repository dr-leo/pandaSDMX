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
def test_read_xml(req, path):
    req.get(fromfile=path).msg


# Read example structure files
@pytest.mark.parametrize('path', test_structure)
def test_read_xml_structure(req, path):
    req.get(fromfile=path).msg


def test_read_xml_structure_insee(req):
    msg = req.get(fromfile=test_structure[4]).msg

    # Same objects referenced
    assert (id(msg.dataflow['IPI-2010-A21'].structure) ==
            id(msg.structure['IPI-2010-A21']))

    # Number of dimensions loaded correctly
    dsd = msg.structure['IPI-2010-A21']
    assert len(dsd.dimensions) == 4
