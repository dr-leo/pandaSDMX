"""Tests against the actual APIs for specific data sources.

HTTP responses from the data sources are cached in tests/data/cache.
To force the data to be retrieved over the Internet, delete this directory.
"""
# TODO add a pytest argument for clearing this cache in conftest.py
import logging

from pandasdmx.api import Request
from pandasdmx.exceptions import HTTPError
from pandasdmx.source import DataContentType, sources
from pandasdmx.util import Resource
import pytest
import requests_mock

from . import test_data_path


log = logging.getLogger(__name__)


structure_endpoints = list(filter(lambda r: r != Resource.data, Resource))


def pytest_generate_tests(metafunc):
    """pytest hook for parametrizing tests with 'endpoint' arguments."""
    if 'endpoint' not in metafunc.fixturenames:
        return  # Don't need to parametrize this metafunc

    endpoints = []

    # SDMX-JSON sources do not support structure queries
    source = sources[metafunc.cls.source_id]
    if source.data_content_type == DataContentType.JSON:
        metafunc.parametrize('endpoint', endpoints)
        return

    # This exception is raised by api.Request._request_from_args
    # TODO parametrize force=True to query these endpoints anyway; then CI
    #      XPASS will reveal when data sources change their support for
    #      endpoints
    mark_unsupported = pytest.mark.xfail(
        strict=True,
        reason='Known non-supported endpoint.',
        raises=NotImplementedError)

    for ep in structure_endpoints:
        # Accumulate multiple marks; first takes precedence
        marks = []

        # Check if the associated source supports the endpoint
        supported = source.supports[ep]
        if not supported:
            marks.append(mark_unsupported)

        # Check if the test function's class contains an expected failure
        # for this endpoint
        exc_class = metafunc.cls.xfail.get(ep.name, None)
        if exc_class:
            # Mark the test as expected to fail
            marks.append(pytest.mark.xfail(strict=True, raises=exc_class))

            if not supported:
                log.info(f'tests for {metafunc.cls.source_id!r} mention '
                         f'unsupported endpoint {ep.name!r}')

        # Tolerate 503 errors
        if metafunc.cls.tolerate_503:
            marks.append(
                pytest.mark.xfail(
                    raises=HTTPError,
                    reason='503 Server Error: Service Unavailable')
                )

        endpoints.append(pytest.param(ep, marks=marks))

    # Run the test function once for each endpoint
    metafunc.parametrize('endpoint', endpoints)


class DataSourceTest:
    """Base class for data source tests."""
    # TODO also test data endpoints
    # TODO also test structure-specific data

    # Must be one of the IDs in sources.json
    source_id = None

    # Mapping of endpoint → Exception subclass.
    # Tests of these endpoints are expected to fail.
    xfail = {}

    # True to xfail if a 503 Error is returned
    tolerate_503 = False

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


class TestABS(DataSourceTest):
    source_id = 'ABS'


class TestECB(DataSourceTest):
    source_id = 'ECB'
    xfail = {
        # 404 Client Error: Not Found
        'provisionagreement': HTTPError,
        }


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
            # str() here is for Python 3.5 compatibility
            args['body'] = open(str(args['body']), 'rb')
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


class TestILO(DataSourceTest):
    source_id = 'ILO'

    xfail = {
        # 413 'Too many results, please specify codelist ID'
        'codelist': HTTPError,
        }

    @pytest.mark.remote_data
    def test_codelist(self, req):
        req.get('codelist', 'CL_ECO',
                tofile=self._cache_path.with_suffix('.' + 'codelist-CL_ECO'))


class TestINEGI(DataSourceTest):
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
    xfail = {
        # 400 Bad Request
        'provisionagreement': HTTPError,
        }

    @pytest.mark.remote_data
    def test_endpoints(self, req, endpoint):
        # Using the default 'INSEE' agency in the URL gives a response "La
        # syntaxe de la requête est invalide."
        req.get(endpoint, provider='all',
                tofile=self._cache_path.with_suffix('.' + endpoint))


class TestISTAT(DataSourceTest):
    source_id = 'ISTAT'

    @pytest.mark.remote_data
    def test_gh_75(self, req):
        """Test of https://github.com/dr-leo/pandaSDMX/pull/75."""

        df_id = '47_850'

        # Reported Dataflow query works
        df = req.dataflow(df_id).dataflow[df_id]

        # dict() key for the query
        data_key = dict(FREQ=['A'], ITTER107=['001001'], SETTITOLARE=['1'],
                        TIPO_DATO=['AUTP'], TIPO_GESTIONE=['ALL'],
                        TIPSERVSOC=['ALL'])

        # Dimension components are in the correct order
        assert [dim.id for dim in df.structure.dimensions.components] == \
            list(data_key.keys()) + ['TIME_PERIOD']

        # Reported data query works
        req.data(df_id, key='A.001001+001002.1.AUTP.ALL.ALL')

        # Use a dict() key to force Request to make a sub-query for the DSD
        req.data(df_id, key=data_key)


class TestNB(DataSourceTest):
    source_id = 'NB'
    # This source returns a valid SDMX Error message (100 No Results Found)
    # for the 'categoryscheme' endpoint.


class TestOECD(DataSourceTest):
    source_id = 'OECD'


class TestSGR(DataSourceTest):
    source_id = 'SGR'


class TestUNESCO(DataSourceTest):
    source_id = 'UNESCO'
    xfail = {
        # Requires registration
        'categoryscheme': HTTPError,
        'codelist': HTTPError,
        'conceptscheme': HTTPError,
        'dataflow': HTTPError,
        'provisionagreement': HTTPError,

        # Because 'supports_series_keys_only' was set
        # TODO check
        # 'datastructure': NotImplementedError,
        }


class TestUNSD(DataSourceTest):
    source_id = 'UNSD'


class TestWB(DataSourceTest):
    source_id = 'WB'
