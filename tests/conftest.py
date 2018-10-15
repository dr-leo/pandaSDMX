import pytest

from pandasdmx.api import Request


@pytest.fixture
def empty_req():
    return Request()
