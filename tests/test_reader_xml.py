import warnings

import pytest

from . import test_data_path, test_files


warnings.filterwarnings('error')


# Read example data files
@pytest.mark.parametrize('path', **test_files(format='xml', kind='data'))
def test_read_xml(req, path):
    req.get(fromfile=path).msg


# Read example structure files
@pytest.mark.parametrize('path', **test_files(format='xml', kind='structure'))
def test_read_xml_structure(req, path):
    req.get(fromfile=path).msg


def test_read_xml_structure_insee(req):
    msg = req.get(fromfile=test_data_path / 'insee' /
                  'insee-IPI-2010-A21-datastructure.xml').msg

    # Same objects referenced
    assert (id(msg.dataflow['IPI-2010-A21'].structure) ==
            id(msg.structure['IPI-2010-A21']))

    # Number of dimensions loaded correctly
    dsd = msg.structure['IPI-2010-A21']
    assert len(dsd.dimensions) == 4
