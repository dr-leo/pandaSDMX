"""Tests of data from specific agencies.

HTTP responses from the agency APIs are cached in tests/data/cache.
To force the data to be retrieved over the Internet, delete this directory.
"""
# TODO add a pytest argument for clearing this cache in conftest.py

import pytest

from pandasdmx.api import Request
from pandasdmx.reader.sdmxml import ParseError
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
    xfail = {
        # KeyError: 'code' in reader.sdmxml.parse_codelist()
        'codelist': ParseError,
        # AttributeError: parse_groupdimension
        'conceptscheme': ParseError,
        # ParseError: <Concept: 'FREQ'=''> not located in
        #             <ConceptScheme: 'ECB_CONCEPTS', 0 items>
        'dataflow': ParseError,
        'datastructure': ParseError,
        }


class TestESTAT(AgencyTest):
    agency_id = 'ESTAT'
    xfail = {
        # 501 Server Error: Not Implemented
        'categoryscheme': HTTPError,
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        # 404 Client Error: Not Found
        'datastructure': HTTPError,
        }


class TestIMF(AgencyTest):
    agency_id = 'IMF_SDMXCENTRAL'
    xfail = {
        # AttributeError: parse_contact
        'categoryscheme': ParseError,
        'codelist': ParseError,
        'conceptscheme': ParseError,
        'dataflow': ParseError,
        'datastructure': ParseError,
    }


class TestINSEE(AgencyTest):
    agency_id = 'INSEE'
    xfail = {
        # 400 Client Error
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,
        'datastructure': HTTPError,
        }


class TestOECD(AgencyTest):
    agency_id = 'OECD'
    xfail = {
        # 404 Client Error: Not Found
        'categoryscheme': HTTPError,
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,
        'datastructure': HTTPError,
        }


class TestSGR(AgencyTest):
    agency_id = 'SGR'
    xfail = {
        # Missing content-type header in response
        'categoryscheme': KeyError,
        # 404 Client Error: Not Found
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,
        'datastructure': HTTPError,
        }


class TestUNESCO(AgencyTest):
    agency_id = 'UNESCO'
    xfail = {
        'categoryscheme': HTTPError,
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,
        'datastructure': HTTPError,
        }


class TestUNSD(AgencyTest):
    agency_id = 'UNSD'
    xfail = {
        # ParseError: <Concept: 'FREQ'=''> not located in
        #             <ConceptScheme: 'MDG_DATA_CONCEPTS', 0 items>
        'datastructure': ParseError,
        }


class TestWB(AgencyTest):
    agency_id = 'WBG_WITS'
    xfail = {
        # KeyError 'concept' in reader.sdmxml.parse_conceptscheme()
        'conceptscheme': ParseError,
        # ParseError: <Concept: 'FREQ'=''> not located in
        #             <ConceptScheme: 'TARIFF_CONCEPTS', 0 items>
        'datastructure': ParseError,
        }
