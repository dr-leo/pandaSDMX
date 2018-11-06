import pytest

from pandasdmx.api import Request


@pytest.fixture
def req():
    """An empty Request object."""
    return Request()
