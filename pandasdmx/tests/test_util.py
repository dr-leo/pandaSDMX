import pydantic
import pytest
from pydantic import StrictStr

from sdmx.util import BaseModel, DictLike, validate_dictlike


def test_dictlike():
    dl = DictLike()

    # Set by item name
    dl["TIME_PERIOD"] = 3
    dl["CURRENCY"] = "USD"

    # Access by attribute name
    assert dl.TIME_PERIOD == 3

    # Access by item index
    assert dl[1] == "USD"

    # Access beyond index
    with pytest.raises(KeyError):
        dl["FOO"]

    with pytest.raises(IndexError):
        dl[2]

    with pytest.raises(AttributeError):
        dl.FOO


def test_dictlike_anno():
    @validate_dictlike("items")
    class Foo(BaseModel):
        items: DictLike[StrictStr, int] = DictLike()

    f = Foo()
    assert type(f.items) == DictLike

    # Can be set with DictLike
    f.items = DictLike(a=1, b=2)
    assert type(f.items) == DictLike

    # Can be set with dict()
    f.items = {"a": 1, "b": 2}
    assert type(f.items) == DictLike

    # Type checking on creation
    with pytest.raises(pydantic.ValidationError):
        f = Foo(items={1: "a"})

    # Type checking on assignment
    f = Foo()
    with pytest.raises(pydantic.ValidationError):
        f.items = {1: "a"}

    # Type checking on setting elements
    f = Foo(items={"a": 1})
    with pytest.raises(pydantic.ValidationError):
        f.items[123] = 456

    # commented: this does not work, since validate_dictlike does not operate
    # until initial values are assigned to the field
    # f = Foo()
    # with pytest.raises(pydantic.ValidationError):
    #     f.items[123] = 456

    # Use validate_dictlike() twice
    @validate_dictlike("elems")
    class Bar(BaseModel):
        elems: DictLike[StrictStr, float] = DictLike()
