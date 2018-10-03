from pandasdmx.model import DataSet
from pandasdmx.writer.data2pandas import Writer


def test_dataset_bare():
    # Create a bare dataset
    ds = DataSet()

    # Populate with observations
    # TODO

    # Write to pd.Dataframe
    Writer().write(ds)
