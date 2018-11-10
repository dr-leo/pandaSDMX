import pytest
from . import test_data_path, test_files

from pandasdmx.writer.structure2pd import Writer


@pytest.fixture
def dsd_common():
    from pandasdmx.reader.sdmxml import Reader
    fd = open(test_data_path / 'common' / 'common.xml')
    return Reader(None).initialize(fd)


@pytest.mark.xfail(reason='writer.structure2pd needs refactor')
def test_writer(dsd_common):
    Writer(None).write(dsd_common)


@pytest.mark.parametrize('path', **test_files(kind='structure'))
def test_writer_many(path):
    from pandasdmx.reader.sdmxml import Reader
    msg = Reader(None).initialize(open(path))
    Writer(None).write(msg)
