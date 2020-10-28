"""Specimens and other data for tests.

This directory contains files with SDMX data and structure messages, in both
SDMX-ML ('.xml') and JSON ('.json') formats.

These files can be:
- retrieved with :meth:`specimen`,
- used to parametrize test methods with :meth:`test_data`, and
- compared to expected :meth:`to_pandas` output using :meth:`expected_data`.

The files are:

- Arranged in directories with names matching particular sources in
  :file:`sources.json`.

- Named with:

  - Certain keywords:

    - '-structure': a structure message, often associated with a file with a
      similar name containing a data message.
    - 'ts': time-series data, i.e. with a TimeDimensions at the level of
      individual Observations.
    - 'xs': cross-sectional data arranged in other ways.
    - 'flat': flat DataSets with all Dimensions at the Observation level.
    - 'ss': structure-specific data messages.

  - In some cases, the query string or data flow/structure ID as the file name.

  - Hyphens '-' instead of underscores '_'.

"""
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

BASE_PATH = Path(__file__).parent

# List of specimen files.
# Each is a tuple: (path, format (xml|json), kind (data|structure))
TEST_FILES = [
    (BASE_PATH / "INSEE" / "CNA-2010-CONSO-SI-A17.xml", "xml", "data"),
    (BASE_PATH / "INSEE" / "IPI-2010-A21.xml", "xml", "data"),
]

# XML data files for the ECB exchange rate data flow
for path in (BASE_PATH / "ECB_EXR").rglob("*.xml"):
    kind = "data"
    if "structure" in path.name or "common" in path.name:
        kind = "structure"
    TEST_FILES.append((path, "xml", kind))

# JSON data files for the ECB exchange rate data flow
for fp in (BASE_PATH / "ECB_EXR").rglob("*.json"):
    TEST_FILES.append((fp, "json", "data"))

# Miscellaneous XML data files
TEST_FILES.append((BASE_PATH / "ESTAT" / "footer.xml", "xml", "data"))


# Miscellaneous XML structure files
TEST_FILES.extend(
    (BASE_PATH.joinpath(*parts), "xml", "structure")
    for parts in [
        ("ECB", "orgscheme.xml"),
        ("ESTAT", "apro_mk_cola-structure.xml"),
        # Manually reduced subset of the response for this DSD. Test for
        # <str:CubeRegion> containing both <com:KeyValue> and <com:Attribute>
        ("IMF", "ECOFIN_DSD-structure.xml"),
        ("INSEE", "CNA-2010-CONSO-SI-A17-structure.xml"),
        ("INSEE", "dataflow.xml"),
        ("INSEE", "IPI-2010-A21-structure.xml"),
        ("ISTAT", "47_850-structure.xml"),
        ("UNSD", "codelist_partial.xml"),
        ("SGR", "common-structure.xml"),
    ]
)

# Expected to_pandas() results for data files above; see expected_data()
# - Keys are the file name (above) with '.' -> '-': 'foo.xml' -> 'foo-xml'
# - Data is stored in expected/{KEY}.txt
# - Values are either argument to pd.read_csv(); or a dict(use='other-key'),
#   in which case the info for other-key is used instead.
EXPECTED = {
    "ng-flat-xml": dict(index_col=[0, 1, 2, 3, 4, 5]),
    "ng-ts-gf-xml": dict(use="ng-flat-xml"),
    "ng-ts-xml": dict(use="ng-flat-xml"),
    "ng-xs-xml": dict(index_col=[0, 1, 2, 3, 4, 5]),
    # Excluded: this file contains two DataSets, and expected_data() currently
    # only supports specimens with one DataSet
    # 'action-delete-json': dict(header=[0, 1, 2, 3, 4]),
    "xs-json": dict(index_col=[0, 1, 2, 3, 4, 5]),
    "flat-json": dict(index_col=[0, 1, 2, 3, 4, 5]),
    "ts-json": dict(use="flat-json"),
}


def test_files(format=None, kind=None):
    """Generate a sequence of test file paths matching criteria.

    The return value should be passed as kwargs to pytest.mark.parametrize():

        pytest.mark.parametrize('argname', **test_files(…))

    """
    result = dict(argvalues=[], ids=[])
    for path, f, k in TEST_FILES:
        if (format and format != f) or (kind and kind != k):
            continue
        result["argvalues"].append(path)
        result["ids"].append(path.name)
    return result


@contextmanager
def specimen(pattern="", opened=True):
    """Open the test specimen file with *pattern* in the name."""
    for path, f, k in TEST_FILES:
        if path.match("*" + pattern + "*"):
            yield open(path, "br") if opened else path
            return
    raise ValueError(pattern)


def expected_data(path):
    """Return the expected to_pandas() result for *path*."""
    try:
        key = path.name.replace(".", "-")
        info = EXPECTED[key]
        if "use" in info:
            # Use the same expected data as another file
            key = info["use"]
            info = EXPECTED[key]
    except KeyError:
        return None

    args = dict(sep=r"\s+", index_col=[0], header=[0])
    args.update(info)

    expected_path = (BASE_PATH / "expected" / key).with_suffix(".txt")
    result = pd.read_csv(expected_path, **args)

    # A series; unwrap
    if set(result.columns) == {"value"}:
        result = result["value"]

    return result
