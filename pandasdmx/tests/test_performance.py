"""Speed and memory usage tests."""
from sdmx.model import AttributeValue, DataAttribute, DataStructureDefinition


def test_refcount():
    # Component (subclasses) created outside of a DataStructureDefinition
    da1 = DataAttribute(id="foo")
    da2 = DataAttribute(id="foo")

    assert id(da1) != id(da2)
    assert da1 is not da2

    # Retrieving attributes from a DataStructureDefinition results in references
    # to the same object
    dsd = DataStructureDefinition()

    da3 = dsd.attributes.getdefault("foo")
    da4 = dsd.attributes.getdefault("foo")

    assert id(da3) == id(da4)
    assert da3 is da4
    assert len(dsd.attributes) == 1

    # Creating an AttributeValue referencing a DataAttribute outside a DSD
    av1 = AttributeValue(value="baz", value_for=DataAttribute(id="foo"))
    assert not any([av1.value_for is da for da in (da1, da2, da3)])

    # Same, using a DSD
    av2 = AttributeValue(value="baz", value_for="foo", dsd=dsd)
    assert av2.value_for is da3
