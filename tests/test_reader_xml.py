import warnings

import pandasdmx as sdmx
import pytest

from . import test_data_path, test_files


warnings.filterwarnings('error')


# Read example data files
@pytest.mark.parametrize('path', **test_files(format='xml', kind='data'))
def test_read_xml(path):
    sdmx.read_sdmx(path)


# Read example structure files
@pytest.mark.parametrize('path', **test_files(format='xml', kind='structure'))
def test_read_xml_structure(path):
    sdmx.read_sdmx(path)


def test_read_xml_structure_insee():
    msg = sdmx.read_sdmx(test_data_path / 'insee' /
                         'insee-IPI-2010-A21-datastructure.xml')

    # Same objects referenced
    assert (id(msg.dataflow['IPI-2010-A21'].structure) ==
            id(msg.structure['IPI-2010-A21']))

    # Number of dimensions loaded correctly
    dsd = msg.structure['IPI-2010-A21']
    assert len(dsd.dimensions) == 4


# Read structure-specific messages
def test_read_ss_xml():
    base_path = test_data_path / 'exr' / '1'
    dsd_path = base_path / 'structure.xml'
    msg_path = base_path / 'M.USD.EUR.SP00.A.xml'

    # Read the DSD
    dsd = sdmx.read_sdmx(dsd_path).structure['ECB_EXR1']

    # Read a data message
    msg = sdmx.read_sdmx(msg_path, dsd=dsd)

    # The dataset in the message is structured by the DSD
    assert msg.data[0].structured_by is dsd

    # TODO test that the contents of the DSD (Dimensions, etc.) are the same
    #      referenced by the objects in the data message
