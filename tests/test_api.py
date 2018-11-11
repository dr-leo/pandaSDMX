from io import StringIO
from json import JSONDecodeError
import logging

from pytest import raises

from pandasdmx.api import Request


def test_request():
    # Constructor
    r = Request(log_level=logging.ERROR)

    # Invalid agency name (replaces former test_request.py)
    with raises(ValueError):
        Request('noagency')

    # Class methods

    # list_agencies()
    Request.list_agencies()

    # load_agency_profile()
    with raises(JSONDecodeError):
        Request.load_agency_profile('FOO')

    # with empty JSON
    tmp = StringIO('{}')
    Request.load_agency_profile(tmp)

    # Regular methods
    r.clear_cache()

    r.timeout = 300
    assert r.timeout == 300
