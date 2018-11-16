"""Tests of data from specific agencies.

HTTP responses from the agency APIs are cached in tests/data/cache.
To force the data to be retrieved over the Internet, delete this directory.
"""
# TODO add a pytest argument for clearing this cache in conftest.py
from json import JSONDecodeError

from pandasdmx.api import Request
from pandasdmx.reader.sdmxml import ParseError
import pytest
from requests.exceptions import HTTPError

from . import test_data_path


structure_endpoints = [
    'categoryscheme',
    'codelist',
    'conceptscheme',
    'dataflow',
    'datastructure',
    ]


def pytest_generate_tests(metafunc):
    """pytest hook for parametrizing tests with 'endpoint' arguments."""
    if 'endpoint' in metafunc.fixturenames:
        endpoints = []
        for ep in structure_endpoints:
            # Check if the test function's class contains an expected failure
            # for this endpoint
            exc_class = metafunc.cls.xfail.get(ep, None)
            if exc_class:
                # Mark the test as expected to fail
                mark = pytest.mark.xfail(strict=True, raises=exc_class)
                endpoints.append(pytest.param(ep, marks=mark))
            else:
                # No expected failure; use the bare string as an argument
                endpoints.append(ep)

        # Run the test function once for each endpoint
        metafunc.parametrize('endpoint', endpoints)


class AgencyTest:
    """Base class for agency tests."""
    # Must be one of the IDs in agencies.json
    agency_id = None

    # Mapping of endpoint → Exception subclass.
    # Tests of these endpoints are expected to fail.
    xfail = {}

    @pytest.fixture
    def req(self):
        # Use a common cache file for all agency tests
        (test_data_path / 'cache').mkdir(exist_ok=True)
        self._cache_path = test_data_path / 'cache' / self.agency_id
        return Request(self.agency_id, cache_name=str(self._cache_path),
                       backend='sqlite')

    @pytest.mark.remote_data
    def test_common_structure_endpoints(self, req, endpoint):
        # See pytest_generate_tests() for values of 'endpoint'
        req.get(endpoint, tofile=self._cache_path.with_suffix('.' + endpoint))


class TestABS(AgencyTest):
    agency_id = 'ABS'
    xfail = {
        # These 3 endpoints return a content-type: text/html response saying
        # the endpoint is not implemented
        'categoryscheme': ValueError,
        'codelist': ValueError,
        'conceptscheme': ValueError,

        # 400 Client Error: Semantic Error
        'dataflow': HTTPError,

        # 404 Client Error: Not Found
        'datastructure': HTTPError,
        }


class TestECB(AgencyTest):
    agency_id = 'ECB'


class TestESTAT(AgencyTest):
    agency_id = 'ESTAT'
    xfail = {
        'categoryscheme': NotImplementedError,
        'codelist': NotImplementedError,
        'conceptscheme': NotImplementedError,

        # 404 Client Error: Not Found
        # NOTE the ESTAT service does not give a general response that contains
        #      all datastructures; this is really more of a 501.
        'datastructure': HTTPError,
        }


class TestIMF(AgencyTest):
    agency_id = 'IMF_SDMXCENTRAL'
    xfail = {
        # ParseError: <Category: 'ESA2010MA.A'=''> not located in
        #             <CategoryScheme: 'ESA2010TP', 7 items>
        # NB this object exists, but its ID is understood as simply 'A', rather
        #    than '{parent_id}.A'.
        'categoryscheme': ParseError,

        # TypeError: cannot instantiate from string class name: Code
        # structure > structures > codelists (skip) > codelist > code > parent
        'codelist': ParseError,

        # AttributeError: 'Reader' object has no attribute
        #                 'parse_enumerationformat'
        'datastructure': ParseError,
        }


class TestINSEE(AgencyTest):
    agency_id = 'INSEE'


class TestOECD(AgencyTest):
    agency_id = 'OECD'
    xfail = {
        # can't determine a reader for response content type: text/html
        # NOTE these are Microsoft IIS HTML error pages for 404 errors
        'categoryscheme': ValueError,
        'codelist': ValueError,
        'conceptscheme': ValueError,
        'datastructure': ValueError,

        # Expecting value: line 1 column 1 (char 0)
        # NOTE this is actually a plain-text error response
        'dataflow': JSONDecodeError,
        }


class TestSGR(AgencyTest):
    agency_id = 'SGR'
    xfail = {
        # See IMF xfail for categoryscheme; same issue, this time with key
        # ESA2010MA.Q
        'categoryscheme': ParseError,
        }

    # Based on query builder at
    # https://registry.sdmx.org/FusionRegistry/rest-get.html
    @pytest.mark.remote_data
    def test_structure_codelist(self, req):
        req.get(resource_type='codelist',
                resource_id='all',
                agency='all',
                tofile=self._cache_path.with_suffix('.codelist2'))


class TestUNESCO(AgencyTest):
    agency_id = 'UNESCO'
    xfail = {
        # Requires registration
        'categoryscheme': HTTPError,
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,
        'datastructure': HTTPError,
        }


class TestUNSD(AgencyTest):
    agency_id = 'UNSD'


class TestWB(AgencyTest):
    agency_id = 'WBG_WITS'
