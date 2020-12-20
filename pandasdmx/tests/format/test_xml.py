from pandasdmx import model
from pandasdmx.format import xml


def test_tag_for_class():
    # ItemScheme is never written to XML; no corresponding tag name
    assert xml.tag_for_class(model.ItemScheme) is None
