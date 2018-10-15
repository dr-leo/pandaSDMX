from json import JSONDecodeError
import logging

from pytest import raises

from pandasdmx.api import Request

from . import test_data_path


def test_request():
    # Constructor
    r = Request(log_level=logging.DEBUG)

    # Invalid agency name (replaces former test_request.py)
    with raises(ValueError):
        Request('noagency')

    # Class methods

    # list_agencies()
    Request.list_agencies()

    # load_agency_profile()
    with raises(JSONDecodeError):
        Request.load_agency_profile('FOO')

    # Regular methods
    r.clear_cache()

    r.timeout = 300
    assert r.timeout == 300


def test_response():
    # Constructor
    req = Request()
    resp = req.get(fromfile=test_data_path / 'exr' / 'ecb_exr_ng' / 'generic' /
                   'ecb_exr_ng_flat.xml')

    # write() with no argument
    resp.write()
