"""Tests against the actual APIs for specific data sources.

HTTP responses from the data sources are cached in tests/data/cache.
To force the data to be retrieved over the Internet, delete this directory.
"""
# TODO add a pytest argument for clearing this cache in conftest.py
from pandasdmx.api import Request
from pandasdmx.reader import ParseError
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


class DataSourceTest:
    """Base class for data source tests."""
    # Must be one of the IDs in agencies.json
    source_id = None

    # Mapping of endpoint → Exception subclass.
    # Tests of these endpoints are expected to fail.
    xfail = {}

    @pytest.fixture
    def req(self):
        # Use a common cache file for all agency tests
        (test_data_path / 'cache').mkdir(exist_ok=True)
        self._cache_path = test_data_path / 'cache' / self.source_id
        return Request(self.source_id, cache_name=str(self._cache_path),
                       backend='sqlite')

    @pytest.mark.remote_data
    def test_endpoints(self, req, endpoint):
        # See pytest_generate_tests() for values of 'endpoint'
        req.get(endpoint, tofile=self._cache_path.with_suffix('.' + endpoint))


class JSONDataSourceTest(DataSourceTest):
    # SDMX-JSON sources do not provide structure endpoints
    xfail = {
        'categoryscheme': ValueError,
        'codelist': ValueError,
        'conceptscheme': ValueError,
        'dataflow': ValueError,
        'datastructure': ValueError,
        }


class TestABS(JSONDataSourceTest):
    source_id = 'ABS'


class TestECB(DataSourceTest):
    source_id = 'ECB'


# Data for requests_mock; see TestESTAT.mock()
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


class TestESTAT(DataSourceTest):
    source_id = 'ESTAT'
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
        req = Request(self.source_id)

        with mock:
            msg = req.get(url=list(estat_mock.keys())[0],
                          get_footer_url=(1, 1))

        assert len(msg.data[0].obs) == 43


class TestIMF(DataSourceTest):
    source_id = 'IMF'
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


class TestILO(DataSourceTest):
    source_id = 'ILO'
    xfail = {
        'categoryscheme': HTTPError,  # 501 'Resolve parents not supported'

        # 413 'Too many results, please specify codelist ID'
        'codelist': HTTPError,

        # Returns SDMXML v2.0 messages
        'conceptscheme': ParseError,
        'dataflow': ParseError,
        'datastructure': ParseError,
        }

    @pytest.mark.xfail(reason='ILO returns SDMXML v2.0 messages.')
    @pytest.mark.remote_data
    def test_categoryscheme(self, req):
        # Identical to DataSourceTest.test_endpoints, except
        # params={} is passed to suppress the automatic addition of
        # ?references=parentsandsiblings
        #
        # Valid values are: none, parents, parentsandsiblings, children,
        # descendants, all, or a specific structure reference such as
        # 'codelist'
        req.get('categoryscheme',
                tofile=self._cache_path.with_suffix('.' + 'categoryscheme'),
                params={'references': 'children'})

    @pytest.mark.xfail(reason='ILO returns SDMXML v2.0 messages.')
    @pytest.mark.remote_data
    def test_codelist(self, req):
        req.get('codelist', 'CL_ECO',
                tofile=self._cache_path.with_suffix('.' + 'codelist-CL_ECO'))


class TestINEGI(DataSourceTest):
    # TODO also test INEGI_S
    source_id = 'INEGI'

    @pytest.mark.remote_data
    def test_endpoints(self, req, endpoint):
        # SSL certificate verification currently fails for this server; works
        # in Google Chrome
        req.session.verify = False
        # Otherwise identical
        req.get(endpoint, tofile=self._cache_path.with_suffix('.' + endpoint))


class TestINSEE(DataSourceTest):
    source_id = 'INSEE'

    @pytest.mark.remote_data
    def test_endpoints(self, req, endpoint):
        # Using the default 'INSEE' agency in the URL gives a response "La
        # syntaxe de la requête est invalide."
        req.get(endpoint, agency='all',
                tofile=self._cache_path.with_suffix('.' + endpoint))


class TestISTAT(DataSourceTest):
    # TODO also test ISTAT_S
    source_id = 'ISTAT'

    @pytest.mark.remote_data
    def test_endpoints(self, req, endpoint):
        # Using the default 'ISTAT' agency in the URL gives a response "No
        # structures found for the specific query"
        req.get(endpoint, agency='all',
                tofile=self._cache_path.with_suffix('.' + endpoint))


class TestNB(DataSourceTest):
    # TODO also test NB_S
    source_id = 'NB'


class TestOECD(DataSourceTest):
    source_id = 'OECD'


class TestSGR(DataSourceTest):
    source_id = 'SGR'
    xfail = {
        # See IMF xfail for categoryscheme; same issue, this time with key
        # ESA2010MA.Q
        'categoryscheme': ParseError,

        # TODO these are automatically constructed using 'SGR' as the
        # agency_id; this gives 404, as SGR itself is not a data *provider*.
        # However, with 'all', each works. Write tests for these.
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,
        'datastructure': HTTPError,
        }

    # Based on query builder at
    # https://registry.sdmx.org/FusionRegistry/rest-get.html
    @pytest.mark.remote_data
    def test_structure_codelist(self, req):
        req.get(resource_type='codelist',
                resource_id='all',
                agency='all',
                tofile=self._cache_path.with_suffix('.codelist2'))


class TestUNESCO(DataSourceTest):
    source_id = 'UNESCO'
    xfail = {
        # Requires registration
        'categoryscheme': HTTPError,
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,

        # Because 'supports_series_keys_only' was set
        # TODO check
        'datastructure': NotImplementedError,
        }


class TestUNSD(DataSourceTest):
    source_id = 'UNSD'


class TestWB(DataSourceTest):
    source_id = 'WBG_WITS'
