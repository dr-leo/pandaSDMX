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
import requests_mock

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
        'categoryscheme': HTTPError,  # 500 'An error has occurred'
        'codelist': HTTPError,  # 500 'An error has occurred'
        'conceptscheme': HTTPError,  # 500 'An error has occurred'
        'dataflow': HTTPError,  # 400 'Semantic error'
        'datastructure': HTTPError,  # 404 'Not found'
        }


class TestECB(AgencyTest):
    agency_id = 'ECB'


estat_mock = {
    ('http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/nama_10_gdp/'
     '..B1GQ+P3.'): {
        'body': test_data_path / 'estat' / 'footer2.xml',
        'headers': {
            'Content-Type':
                'application/vnd.sdmx.genericdata+xml; version=2.1',
            },
        },
    'http://ec.europa.eu/eurostat/SDMX/diss-web/file/7JUdWyAy4fmjBSWT': {
        # This file is a trimmed version of the actual response for the above
        # query
        'body': test_data_path / 'estat' / 'footer2.zip',
        'headers': {
            'Content-Type': 'application/octet-stream',
            },
        },
    }


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

    @pytest.fixture
    def mock(self):
        # Prepare the mock requests
        fixture = requests_mock.Mocker()
        for url, args in estat_mock.items():
            args['body'] = open(args['body'], 'rb')
            fixture.get(url, **args)

        return fixture

    def test_xml_footer(self, mock):
        req = Request(self.agency_id)

        with mock:
            msg = req.get(url=list(estat_mock.keys())[0],
                          get_footer_url=(1, 1))

        assert len(msg.data[0].obs) == 43


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
