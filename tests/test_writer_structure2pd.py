import pytest
from . import test_data_path

from pandasdmx.writer.structure2pd import Writer


@pytest.fixture
def dsd_common():
    from pandasdmx.reader.sdmxml import Reader
    fd = open(test_data_path / 'common' / 'common.xml')
    return Reader(None).initialize(fd)


@pytest.mark.xfail(reason='writer.structure2pd needs refactor')
def test_writer(dsd_common):
    Writer(None).write(dsd_common)
