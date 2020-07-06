"""Tests against the actual APIs for specific data sources.

HTTP responses from the data sources are cached in tests/data/cache.
To force the data to be retrieved over the Internet, delete this directory.
"""
# TODO add a pytest argument for clearing this cache in conftest.py
import logging
import os
from typing import Any, Dict, Type

import pytest
import requests_mock

import sdmx
from sdmx import Resource
from sdmx.api import Request
from sdmx.exceptions import HTTPError
from sdmx.source import DataContentType, sources

from .data import BASE_PATH as TEST_DATA_PATH
from .data import specimen

log = logging.getLogger(__name__)


pytestmark = pytest.mark.skipif(
    # Default value in get() ensures that when *not* on Travis, the tests run
    condition=os.environ.get("TRAVIS_EVENT_TYPE", "cron") != "cron",
    # For development/debugging, uncomment the following to *always* run
    # condition=False,
    reason="Fragile source tests only run on Travis for 'cron' events.",
)


def pytest_generate_tests(metafunc):
    """pytest hook for parametrizing tests with 'endpoint' arguments."""
    if "endpoint" not in metafunc.fixturenames:
        return  # Don't need to parametrize this metafunc

    # Arguments to parametrize()
    ep_data = []
    ids = []

    # Use the test class' source_id attr to look up the Source class
    source = sources[metafunc.cls.source_id]

    # This exception is raised by api.Request._request_from_args
    # TODO parametrize force=True to query these endpoints anyway; then CI
    #      XPASS will reveal when data sources change their support for
    #      endpoints
    mark_unsupported = pytest.mark.xfail(
        strict=True, reason="Known non-supported endpoint.", raises=NotImplementedError
    )

    for ep in Resource:
        # Accumulate multiple marks; first takes precedence
        marks = []

        # Check if the associated source supports the endpoint
        supported = source.supports[ep]
        if source.data_content_type == DataContentType.JSON and ep is not Resource.data:
            # SDMX-JSON sources only support data queries
            continue
        elif not supported:
            marks.append(mark_unsupported)

        # Check if the test function's class contains an expected failure
        # for this endpoint
        exc_class = metafunc.cls.xfail.get(ep.name, None)
        if exc_class:
            # Mark the test as expected to fail
            marks.append(pytest.mark.xfail(strict=True, raises=exc_class))

            if not supported:
                log.info(
                    f"tests for {metafunc.cls.source_id!r} mention "
                    f"unsupported endpoint {ep.name!r}"
                )

        # Tolerate 503 errors
        if metafunc.cls.tolerate_503:
            marks.append(
                pytest.mark.xfail(
                    raises=HTTPError, reason="503 Server Error: Service Unavailable"
                )
            )

        # Get keyword arguments for this endpoint
        args = metafunc.cls.endpoint_args.get(ep.name, dict())
        if ep is Resource.data and not len(args):
            # args must be specified for a data query; no args → no test
            continue

        ep_data.append(pytest.param(ep, args, marks=marks))
        ids.append(ep.name)

    # Run the test function once for each endpoint
    metafunc.parametrize("endpoint, args", ep_data, ids=ids)


class DataSourceTest:
    """Base class for data source tests."""

    # TODO also test structure-specific data

    # Must be one of the IDs in sources.json
    source_id: str

    # Mapping of endpoint → Exception subclass.
    # Tests of these endpoints are expected to fail.
    xfail: Dict[str, Type[Exception]] = {}

    # True to xfail if a 503 Error is returned
    tolerate_503 = False

    # Keyword arguments for particular endpoints
    endpoint_args: Dict[str, Dict[str, Any]] = {}

    @pytest.fixture
    def req(self):
        # Use a common cache file for all agency tests
        (TEST_DATA_PATH / ".cache").mkdir(exist_ok=True)
        self._cache_path = TEST_DATA_PATH / ".cache" / self.source_id
        return Request(
            self.source_id, cache_name=str(self._cache_path), backend="sqlite"
        )

    @pytest.mark.network
    def test_endpoints(self, req, endpoint, args):
        # See pytest_generate_tests() for values of 'endpoint'
        cache = self._cache_path.with_suffix(f".{endpoint}.xml")
        result = req.get(endpoint, tofile=cache, **args)

        # For debugging
        # print(cache, cache.read_text(), result, sep='\n\n')
        # assert False

        sdmx.to_pandas(result)

        del result


class TestABS(DataSourceTest):
    source_id = "ABS"


class TestECB(DataSourceTest):
    source_id = "ECB"
    xfail = {
        # 404 Client Error: Not Found
        "provisionagreement": HTTPError
    }


# Data for requests_mock; see TestESTAT.mock()
estat_mock = {
    (
        "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/nama_10_gdp/" "..B1GQ+P3."
    ): {
        "body": TEST_DATA_PATH / "ESTAT" / "footer2.xml",
        "headers": {
            "Content-Type": "application/vnd.sdmx.genericdata+xml; version=2.1"
        },
    },
    "http://ec.europa.eu/eurostat/SDMX/diss-web/file/7JUdWyAy4fmjBSWT": {
        # This file is a trimmed version of the actual response for the above
        # query
        "body": TEST_DATA_PATH / "ESTAT" / "footer2.zip",
        "headers": {"Content-Type": "application/octet-stream"},
    },
}


class TestESTAT(DataSourceTest):
    source_id = "ESTAT"
    xfail = {
        # 404 Client Error: Not Found
        # NOTE the ESTAT service does not give a general response that contains
        #      all datastructures; this is really more of a 501.
        "datastructure": HTTPError
    }

    @pytest.fixture
    def mock(self):
        # Prepare the mock requests
        fixture = requests_mock.Mocker()
        for url, args in estat_mock.items():
            # str() here is for Python 3.5 compatibility
            args["body"] = open(str(args["body"]), "rb")
            fixture.get(url, **args)

        return fixture

    @pytest.mark.network
    def test_xml_footer(self, mock):
        req = Request(self.source_id)

        with mock:
            msg = req.get(url=list(estat_mock.keys())[0], get_footer_url=(1, 1))

        assert len(msg.data[0].obs) == 43

    @pytest.mark.network
    def test_ss_data(self, req):
        """Test a request for structure-specific data.

        Examples from:
        https://ec.europa.eu/eurostat/web/sdmx-web-services/example-queries
        """
        df_id = "nama_10_gdp"
        args = dict(resource_id=df_id)

        # Query for the DSD
        dsd = req.dataflow(**args).dataflow[df_id].structure

        # Even with ?references=all, ESTAT returns a short message with the
        # DSD as an external reference. Query again to get its actual contents.
        if dsd.is_external_reference:
            dsd = req.get(resource=dsd).structure[0]
            print(dsd)

        assert not dsd.is_external_reference

        # Example query, using the DSD already retrieved
        args.update(
            dict(
                key=dict(UNIT=["CP_MEUR"], NA_ITEM=["B1GQ"], GEO=["LU"]),
                params={"startPeriod": "2012", "endPeriod": "2015"},
                dsd=dsd,
                # commented: for debugging
                # tofile='temp.xml',
            )
        )
        req.data(**args)


class TestIMF(DataSourceTest):
    source_id = "IMF"


class TestILO(DataSourceTest):
    source_id = "ILO"

    xfail = {
        # 413 Client Error: Request Entity Too Large
        "codelist": HTTPError
    }

    @pytest.mark.network
    def test_codelist(self, req):
        req.get(
            "codelist",
            "CL_ECO",
            tofile=self._cache_path.with_suffix("." + "codelist-CL_ECO"),
        )


@pytest.mark.xfail(
    reason="500 Server Error returned for all requests.", raises=HTTPError
)
class TestINEGI(DataSourceTest):
    source_id = "INEGI"

    @pytest.mark.network
    def test_endpoints(self, req, endpoint, args):
        # SSL certificate verification sometimes fails for this server; works
        # in Google Chrome
        req.session.verify = False

        # Otherwise identical
        super().test_endpoints(req, endpoint, args)


class TestINSEE(DataSourceTest):
    source_id = "INSEE"

    tolerate_503 = True

    @pytest.mark.network
    def test_endpoints(self, req, endpoint, args):
        # Using the default 'INSEE' agency in the URL gives a response "La
        # syntaxe de la requête est invalide."
        req.get(
            endpoint,
            provider="all",
            **args,
            tofile=self._cache_path.with_suffix("." + endpoint),
        )


@pytest.mark.xfail(reason="Service is currently unavailable.", raises=HTTPError)
class TestISTAT(DataSourceTest):
    source_id = "ISTAT"

    @pytest.mark.network
    def test_gh_75(self, req):
        """Test of https://github.com/dr-leo/pandaSDMX/pull/75."""

        df_id = "47_850"

        # # Reported Dataflow query works
        # df = req.dataflow(df_id).dataflow[df_id]

        with specimen("47_850-structure") as f:
            df = sdmx.read_sdmx(f).dataflow[df_id]

        # dict() key for the query
        data_key = dict(
            FREQ=["A"],
            ITTER107=["001001"],
            SETTITOLARE=["1"],
            TIPO_DATO=["AUTP"],
            TIPO_GESTIONE=["ALL"],
            TIPSERVSOC=["ALL"],
        )

        # Dimension components are in the correct order
        assert [dim.id for dim in df.structure.dimensions.components] == list(
            data_key.keys()
        ) + ["TIME_PERIOD"]

        # Reported data query works
        req.data(df_id, key="A.001001+001002.1.AUTP.ALL.ALL")

        # Use a dict() key to force Request to make a sub-query for the DSD
        req.data(df_id, key=data_key)


class TestNB(DataSourceTest):
    source_id = "NB"
    # This source returns a valid SDMX Error message (100 No Results Found)
    # for the 'categoryscheme' endpoint.


class TestOECD(DataSourceTest):
    source_id = "OECD"

    endpoint_args = {
        "data": dict(
            resource_id="ITF_GOODS_TRANSPORT", key=".T-CONT-RL-TEU+T-CONT-RL-TON"
        )
    }


class TestSGR(DataSourceTest):
    source_id = "SGR"


class TestUNESCO(DataSourceTest):
    source_id = "UNESCO"
    xfail = {
        # Requires registration
        "categoryscheme": HTTPError,
        "codelist": HTTPError,
        "conceptscheme": HTTPError,
        "dataflow": HTTPError,
        "provisionagreement": HTTPError,
        # Because 'supports_series_keys_only' was set
        # TODO check
        # 'datastructure': NotImplementedError,
    }


class TestUNSD(DataSourceTest):
    source_id = "UNSD"


class TestWB(DataSourceTest):
    source_id = "WB"
