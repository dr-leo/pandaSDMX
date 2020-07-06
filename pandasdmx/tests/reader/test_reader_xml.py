import re
from io import BytesIO
from itertools import chain

import pytest
from lxml import etree

import sdmx
from sdmx.format.xml import qname
from sdmx.model import Facet, FacetType, FacetValueType
from sdmx.reader.sdmxml import Reader, XMLParseError
from sdmx.tests.data import specimen, test_files


# Read example data files
@pytest.mark.parametrize("path", **test_files(format="xml", kind="data"))
def test_read_xml(path):
    sdmx.read_sdmx(path)


# Read example structure files
@pytest.mark.parametrize("path", **test_files(format="xml", kind="structure"))
def test_read_xml_structure(path):
    sdmx.read_sdmx(path)


def test_read_xml_structure_insee():
    with specimen("IPI-2010-A21-structure.xml") as f:
        msg = sdmx.read_sdmx(f)

    # Same objects referenced
    assert id(msg.dataflow["IPI-2010-A21"].structure) == id(
        msg.structure["IPI-2010-A21"]
    )

    # Number of dimensions loaded correctly
    dsd = msg.structure["IPI-2010-A21"]
    assert len(dsd.dimensions) == 4


# Read structure-specific messages
def test_read_ss_xml():
    with specimen("M.USD.EUR.SP00.A.xml", opened=False) as f:
        msg_path = f
        dsd_path = f.parent / "structure.xml"

    # Read the DSD
    dsd = sdmx.read_sdmx(dsd_path).structure["ECB_EXR1"]

    # Read a data message
    msg = sdmx.read_sdmx(msg_path, dsd=dsd)
    ds = msg.data[0]

    # The dataset in the message is structured by the DSD
    assert ds.structured_by is dsd

    # Structures referenced in the dataset are from the dsd

    s0_key = list(ds.series.keys())[0]

    # AttributeValue.value_for
    assert s0_key.attrib["DECIMALS"].value_for is dsd.attributes.get("DECIMALS")

    # SeriesKey.described_by
    assert s0_key.described_by is dsd.dimensions

    # Key.described_by
    assert ds.obs[0].key.described_by is dsd.dimensions

    # KeyValue.value_for
    assert ds.obs[0].key.values[0].value_for is dsd.dimensions.get("FREQ")

    # DSD information that is not in the data message can be looked up through
    # navigating object relationships
    TIME_FORMAT = s0_key.attrib["TIME_FORMAT"].value_for
    assert len(TIME_FORMAT.related_to.dimensions) == 5


E = etree.Element

# Each entry is a tuple with 2 elements:
# 1. an instance of lxml.etree.Element to be parsed.
# 2. Either:
#   - A sdmx.model object, in which case the parsed element must match the
#     object.
#   - A string, in which case parsing the element is expected to fail, raising
#     an exception matching the string.
ELEMENTS = [
    # Reader.parse_facet
    (
        E(qname("str:TextFormat"), isSequence="False", startValue="3.4", endValue="1"),
        None,
    ),
    # …attribute names are munged; default textType is supplied
    (
        E(qname("str:EnumerationFormat"), minLength="1", maxLength="6"),
        Facet(
            type=FacetType(min_length=1, max_length=6),
            value_type=FacetValueType["string"],
        ),
    ),
    # …invalid attributes cause an exception
    (
        E(qname("str:TextFormat"), invalidFacetTypeAttr="foo"),
        re.compile("ValidationError: .* extra fields not permitted", flags=re.DOTALL),
    ),
]


@pytest.mark.parametrize(
    "elem, expected", ELEMENTS, ids=list(map(str, range(len(ELEMENTS))))
)
def test_parse_elem(elem, expected):
    """Test individual XML elements.

    This method allows unit-level testing of specific XML elements appearing in
    SDMX-ML messages. Add elements by extending the list passed to the
    parametrize() decorator.
    """
    # Convert to a file-like object compatible with read_message()
    tmp = BytesIO(etree.tostring(elem))

    # Create a reader
    reader = Reader()

    if isinstance(expected, (str, re.Pattern)):
        # Parsing the element raises an exception
        with pytest.raises(XMLParseError, match=expected):
            reader.read_message(tmp)
    else:
        # The element is parsed successfully
        result = reader.read_message(tmp)

        if not result:
            stack = list(chain(*reader.stack.values()))
            assert len(stack) == 1
            result = stack[0]

        if expected:
            # Expected value supplied
            assert expected == result
