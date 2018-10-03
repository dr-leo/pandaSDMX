from unittest import TestCase


class TestAPI(TestCase):
    def test_base_reader_abstract(self):
        """BaseReader cannot be instantiated."""
        from pandasdmx.reader import BaseReader
        with self.assertRaises(TypeError):
            BaseReader(None)

    def test_null_reader(self):
        """Instantiate the null reader."""
        from pandasdmx.reader.null import Reader
        Reader()


def test_dataset_bare():
    from pandasdmx.model import DataSet
    from pandasdmx.writer.data2pandas import Writer

    # Create a bare dataset
    ds = DataSet()

    # Populate with observations
    # TODO

    # Write to pd.Dataframe
    Writer().write(ds)
