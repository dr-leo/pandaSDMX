from pandasdmx.model import DataSet
from pandasdmx.writer.data2pandas import Writer
from unittest import TestCase


class TestAPI(TestCase):
    def test_base_reader_abstract(self):
        """BaseReader cannot be instantiated."""
        from pandasdmx.reader import BaseReader
        with self.assertRaises(TypeError):
            BaseReader(None)


def test_dataset_bare():
    # Create a bare dataset
    ds = DataSet()

    # Populate with observations
    # TODO

    # Write to pd.Dataframe
    Writer().write(ds)
