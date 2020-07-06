"""Tests for pandasdmx/writer.py."""
import pandas as pd
import pytest
from pytest import raises

import sdmx
from sdmx.model import TimeDimension
from sdmx.tests import assert_pd_equal
from sdmx.tests.data import expected_data, specimen, test_files

# file name → (exception raised, exception message, comment/reason)
ssds = (
    "Reading StructureSpecificDataSet does not distinguish between attrs "
    "and dimension values."
)

file_marks = {
    "exr-action-delete.json": (
        AssertionError,
        "Expected type <class 'pandas.core.frame.DataFrame'>, found <class "
        " 'list'> instead",
        "Message contains two DataSets; test infrastructure currently handles "
        "only messages with a single DataSet.",
    ),
    "ECB/EXR/ng-ts-ss.xml": (AssertionError, "Series.index are different", ssds),
    "ECB/EXR/ng-flat-ss.xml": (AssertionError, "Series.index are different", ssds),
    "ECB/EXR/ng-xs-ss.xml": (AssertionError, "Series.index are different", ssds),
    "ECB/EXR/ng-ts-gf-ss.xml": (AssertionError, "Series.index are different", ssds),
}


def pytest_generate_tests(metafunc):
    if "data_path" in metafunc.fixturenames:
        params = []
        tf = test_files(kind="data")
        for value, id in zip(tf["argvalues"], tf["ids"]):
            kwargs = dict(id=id)
            for cond, info in file_marks.items():
                if cond in str(value):
                    kwargs["marks"] = pytest.mark.skip(reason=info[2])
                    break

            params.append(pytest.param(value, **kwargs))

        metafunc.parametrize("data_path", params)


def test_write_data_arguments():
    msg = sdmx.read_sdmx(test_files(kind="data")["argvalues"][0])

    # Attributes must be a string
    with raises(TypeError):
        sdmx.to_pandas(msg, attributes=2)

    # Attributes must contain only 'dgso'
    with raises(ValueError):
        sdmx.to_pandas(msg, attributes="foobarbaz")


def test_write_data(data_path):
    msg = sdmx.read_sdmx(data_path)

    result = sdmx.to_pandas(msg)

    expected = expected_data(data_path)
    if expected is not None:
        print(expected, result, sep="\n")
    assert_pd_equal(expected, result)

    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)


@pytest.mark.parametrize("path", **test_files(kind="data"))
def test_write_data_attributes(path):
    msg = sdmx.read_sdmx(path)

    result = sdmx.to_pandas(msg, attributes="osgd")
    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)


def test_write_agencyscheme():
    # Convert an agency scheme
    with specimen("ECB/orgscheme.xml") as f:
        msg = sdmx.read_sdmx(f)
        data = sdmx.to_pandas(msg)

    assert data["organisation_scheme"]["AGENCIES"]["ESTAT"] == "Eurostat"

    # to_pandas only returns keys for non-empty attributes of StructureMessage
    # https://github.com/dr-leo/pandaSDMX/issues/90
    assert set(data.keys()) == {"organisation_scheme"}

    # Attribute access works
    assert data.organisation_scheme.AGENCIES.ESTAT == "Eurostat"

    with pytest.raises(AttributeError):
        data.codelist
    with pytest.raises(AttributeError):
        data.dataflow
    with pytest.raises(AttributeError):
        data.structure


def test_write_categoryscheme():
    with specimen("IPI-2010-A21-structure.xml") as f:
        msg = sdmx.read_sdmx(f)
        data = sdmx.to_pandas(msg)

    cs = data["category_scheme"]["CLASSEMENT_DATAFLOWS"]

    assert cs.loc["COMPTA-NAT", "name"] == "National accounts (GDP, consumption...)"

    # Children appear
    assert cs.loc["CNA-PIB-2005", "parent"] == "CNA-PIB"


def test_write_codelist():
    # Retrieve codelists from a test specimen and convert to pandas
    with specimen("common-structure.xml") as f:
        dsd_common = sdmx.read_sdmx(f)
    codelists = sdmx.to_pandas(dsd_common)["codelist"]

    # File contains 5 code lists
    assert len(codelists) == 5

    # Code lists have expected number of items
    assert len(codelists["CL_FREQ"]) == 8

    # Items names can be retrieved by ID
    freq = codelists["CL_FREQ"]
    assert freq["A"] == "Annual"

    # Non-hierarchical code list has a string name
    assert freq.name == "Code list for Frequency (FREQ)"

    # Hierarchical code list
    with specimen("codelist_partial.xml") as f:
        msg = sdmx.read_sdmx(f)

    # Convert single codelist
    CL_AREA = sdmx.to_pandas(msg.codelist["CL_AREA"])

    # Hierichical list has a 'parent' column; parent of Africa is the World
    assert CL_AREA.loc["002", "parent"] == "001"

    # Pandas features can be used to merge parent names
    area_hierarchy = pd.merge(
        CL_AREA,
        CL_AREA,
        how="left",
        left_on="parent",
        right_index=True,
        suffixes=("", "_parent"),
    )
    assert area_hierarchy.loc["002", "name_parent"] == "World"


def test_write_conceptscheme():
    with specimen("common-structure.xml") as f:
        msg = sdmx.read_sdmx(f)
        data = sdmx.to_pandas(msg)

    cdc = data["concept_scheme"]["CROSS_DOMAIN_CONCEPTS"]
    assert cdc.loc["UNIT_MEASURE", "name"] == "Unit of Measure"


def test_write_dataflow():
    # Read the INSEE dataflow definition
    with specimen("INSEE/dataflow") as f:
        msg = sdmx.read_sdmx(f)

    # Convert to pandas
    result = sdmx.to_pandas(msg, include="dataflow")

    # Number of Dataflows described in the file
    assert len(result["dataflow"]) == 663

    # ID and names of first Dataflows
    mbop = "Monthly Balance of Payments - "
    expected = pd.Series(
        {
            "ACT-TRIM-ANC": "Activity by sex and age - Quarterly series",
            "BPM6-CCAPITAL": "{}Capital account".format(mbop),
            "BPM6-CFINANCIER": "{}Financial account".format(mbop),
            "BPM6-CTRANSACTION": "{}Current transactions account".format(mbop),
            "BPM6-TOTAL": "{}Overall total and main headings".format(mbop),
        }
    )
    assert_pd_equal(result["dataflow"].head(), expected)


def test_write_dataset_datetime():
    """Test datetime arguments to write_dataset()."""
    # Load structure
    with specimen("IPI-2010-A21-structure.xml") as f:
        dsd = sdmx.read_sdmx(f).structure["IPI-2010-A21"]
        TIME_PERIOD = dsd.dimensions.get("TIME_PERIOD")
        FREQ = dsd.dimensions.get("FREQ")

    assert isinstance(TIME_PERIOD, TimeDimension)

    # Load data, two ways
    with specimen("IPI-2010-A21.xml") as f:
        msg = sdmx.read_sdmx(f, dsd=dsd)
        ds = msg.data[0]
    with specimen("IPI-2010-A21.xml") as f:
        msg_no_structure = sdmx.read_sdmx(f)

    other_dims = list(
        filter(lambda n: n != "TIME_PERIOD", [d.id for d in dsd.dimensions.components])
    )

    def expected(df, axis=0, cls=pd.DatetimeIndex):
        axes = ["index", "columns"] if axis else ["columns", "index"]
        assert getattr(df, axes[0]).names == other_dims
        assert isinstance(getattr(df, axes[1]), cls)

    # Write with datetime=str
    df = sdmx.to_pandas(ds, datetime="TIME_PERIOD")
    expected(df)

    # Write with datetime=Dimension instance
    df = sdmx.to_pandas(ds, datetime=TIME_PERIOD)
    expected(df)

    # Write with datetime=True fails because the data message contains no
    # actual structure information
    with pytest.raises(ValueError, match=r"no TimeDimension in \[.*\]"):
        sdmx.to_pandas(msg_no_structure, datetime=True)
    with pytest.raises(ValueError, match=r"no TimeDimension in \[.*\]"):
        sdmx.to_pandas(msg_no_structure.data[0], datetime=True)

    # DataMessage parsed with a DSD allows write_dataset to infer the
    # TimeDimension
    df = sdmx.to_pandas(msg, datetime=True)
    expected(df)
    # Same for DataSet
    df = sdmx.to_pandas(ds, datetime=True)
    expected(df)

    # As above, with axis=1
    df = sdmx.to_pandas(ds, datetime=dict(dim="TIME_PERIOD", axis=1))
    expected(df, axis=1)
    df = sdmx.to_pandas(ds, datetime=dict(dim=TIME_PERIOD, axis=1))
    expected(df, axis=1)
    ds.structured_by = dsd
    df = sdmx.to_pandas(ds, datetime=dict(axis=1))
    expected(df, axis=1)
    df = sdmx.to_pandas(msg, datetime=dict(axis=1))
    expected(df, axis=1)

    # Write with freq='M' works
    df = sdmx.to_pandas(ds, datetime=dict(dim="TIME_PERIOD", freq="M"))
    expected(df, cls=pd.PeriodIndex)

    # Write with freq='A' works
    df = sdmx.to_pandas(ds, datetime=dict(dim="TIME_PERIOD", freq="A"))
    expected(df, cls=pd.PeriodIndex)
    # …but the index is not unique, because month information was discarded
    assert not df.index.is_unique

    # Write specifying the FREQ dimension by name fails
    with pytest.raises(
        ValueError,
        match="cannot convert to PeriodIndex with " r"non-unique freq=\['A', 'M'\]",
    ):
        sdmx.to_pandas(ds, datetime=dict(dim="TIME_PERIOD", freq="FREQ"))

    # Remove non-monthly obs
    # TODO use a constraint, when this is supported
    ds.obs = list(filter(lambda o: o.key.FREQ != "A", ds.obs))

    # Now specifying the dimension by name works
    df = sdmx.to_pandas(ds, datetime=dict(dim="TIME_PERIOD", freq="FREQ"))

    # and FREQ is no longer in the columns index
    other_dims.pop(other_dims.index("FREQ"))
    expected(df, cls=pd.PeriodIndex)

    # Specifying a Dimension works
    df = sdmx.to_pandas(ds, datetime=dict(dim=TIME_PERIOD, freq=FREQ))
    expected(df, cls=pd.PeriodIndex)

    # As above, using DSD attached to the DataMessage
    df = sdmx.to_pandas(msg, datetime=dict(dim=TIME_PERIOD, freq="FREQ"))
    expected(df, cls=pd.PeriodIndex)

    # Invalid arguments
    with pytest.raises(ValueError, match="X"):
        sdmx.to_pandas(msg, datetime=dict(dim=TIME_PERIOD, freq="X"))
    with pytest.raises(ValueError, match="foo"):
        sdmx.to_pandas(ds, datetime=dict(foo="bar"))
    with pytest.raises(ValueError, match="43"):
        sdmx.to_pandas(ds, datetime=43)


@pytest.mark.parametrize("path", **test_files(kind="structure"))
def test_writer_structure(path):
    msg = sdmx.read_sdmx(path)

    sdmx.to_pandas(msg)

    # TODO test contents


@pytest.mark.network
def test_write_constraint():
    """'constraint' argument to writer.write_dataset."""
    with specimen("ng-ts.xml") as f:
        msg = sdmx.read_sdmx(f)

    # Fetch the message's DSD
    assert msg.structure.is_external_reference
    # NB the speciment included in tests/data has 'ECB_EXR_NG' as the
    #    data structure ID; but a query against the web service gives
    #    'ECB_EXR1' for the same data structure.
    id = "ECB_EXR1"
    dsd = (
        sdmx.Request(msg.structure.maintainer.id).get("datastructure", id).structure[id]
    )

    # Create a ContentConstraint
    cc = dsd.make_constraint({"CURRENCY": "JPY+USD"})

    # Write the message without constraint
    s1 = sdmx.to_pandas(msg)
    assert len(s1) == 12
    assert set(s1.index.to_frame()["CURRENCY"]) == {"CHF", "GBP", "JPY", "USD"}

    # Writing using constraint produces a fewer items; only those matching the
    # constraint
    s2 = sdmx.to_pandas(msg, constraint=cc)
    assert len(s2) == 6
    assert set(s2.index.to_frame()["CURRENCY"]) == {"JPY", "USD"}
