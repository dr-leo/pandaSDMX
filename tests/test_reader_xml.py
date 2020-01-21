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
    ds = msg.data[0]

    # The dataset in the message is structured by the DSD
    assert ds.structured_by is dsd

    # Structures referenced in the dataset are from the dsd

    s0_key = list(ds.series.keys())[0]

    # AttributeValue.value_for
    assert s0_key.attrib['DECIMALS'].value_for \
        is dsd.attributes.get('DECIMALS')

    # SeriesKey.described_by
    assert s0_key.described_by is dsd.dimensions

    # Key.described_by
    assert ds.obs[0].key.described_by is dsd.dimensions

    # KeyValue.value_for
    assert ds.obs[0].key.values[0].value_for \
        is dsd.dimensions.get('FREQ')

    # DSD information that is not in the data message can be looked up through
    # navigating object relationships
    TIME_FORMAT = s0_key.attrib['TIME_FORMAT'].value_for
    assert len(TIME_FORMAT.related_to.dimensions) == 5
