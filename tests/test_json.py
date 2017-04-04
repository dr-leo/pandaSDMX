from os.path import abspath, dirname, join
from unittest import TestCase

from pandasdmx.reader.sdmxjson import Reader
# from pandasdmx.writer.data2pandas import Writer


pkg_path = dirname(abspath(__file__))


class TestJSON(TestCase):

    def setUp(self):
        filepath = join(pkg_path, 'data', 'json', 'exr-flat.json')
        self.source = open(filepath)

    def test_init(self):
        r = Reader(None)
        msg = r.initialize(self.source)
        assert hasattr(msg, 'data')
