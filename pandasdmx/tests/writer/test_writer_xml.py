import logging

import pytest

import sdmx
from sdmx.message import DataMessage
from sdmx.tests.data import specimen

log = logging.getLogger(__name__)


def test_codelist(tmp_path, codelist):
    result = sdmx.to_xml(codelist, pretty_print=True)
    print(result.decode())


def test_structuremessage(tmp_path, structuremessage):
    result = sdmx.to_xml(structuremessage, pretty_print=True)
    print(result.decode())

    # Message can be round-tripped to/from file
    path = tmp_path / "output.xml"
    path.write_bytes(result)
    msg = sdmx.read_sdmx(path)

    # Contents match the original object
    assert (
        msg.codelist["CL_COLLECTION"]["A"].name["en"]
        == structuremessage.codelist["CL_COLLECTION"]["A"].name["en"]
    )

    # False because `structuremessage` lacks URNs, which are constructed automatically
    # by `to_xml`
    assert not msg.compare(structuremessage, strict=True)
    # Compares equal when allowing this difference
    assert msg.compare(structuremessage, strict=False)


_xf_ref = pytest.mark.xfail(
    raises=NotImplementedError, match="Cannot write reference to .* without parent",
)
_xf_not_equal = pytest.mark.xfail(raises=AssertionError)


@pytest.mark.parametrize(
    "specimen_id, strict",
    [
        ("ECB/orgscheme.xml", True),
        ("ECB_EXR/1/structure-full.xml", False),
        ("ESTAT/apro_mk_cola-structure.xml", True),
        pytest.param(
            "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
        ),
        pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
        ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
        ("INSEE/IPI-2010-A21-structure.xml", False),
        pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
        ("SGR/common-structure.xml", True),
        ("UNSD/codelist_partial.xml", True),
    ],
)
def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
    """Test that SDMX-ML StructureMessages can be 'round-tripped'."""

    # Read a specimen file
    with specimen(specimen_id) as f:
        msg0 = sdmx.read_sdmx(f)

    # Write to file
    path = tmp_path / "output.xml"
    path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))

    # Read again
    msg1 = sdmx.read_sdmx(path)

    # Contents are identical
    assert msg0.compare(msg1, strict), (
        path.read_text() if pytestconfig.getoption("verbose") else path
    )


def test_not_implemented():
    msg = DataMessage()

    with pytest.raises(NotImplementedError, match="write DataMessage to XML"):
        sdmx.to_xml(msg)
