import pytest

from pandasdmx.api import Request

structure_endpoints = [
    'categoryscheme',
    'codelist',
    'conceptscheme',
    'dataflow',
    'datastructure',
    ]


class AgencyTest:
    """Fixture for agency tests."""
    agency_id = None

    @pytest.fixture
    def req(self):
        return Request(self.agency_id)

    @pytest.mark.remote_data
    @pytest.mark.parametrize('endpoint', structure_endpoints)
    def test_common_structure_endpoints(self, req, endpoint):
        req.get(endpoint)


class TestABS(AgencyTest):
    agency_id = 'ABS'


class TestECB(AgencyTest):
    agency_id = 'ECB'


class TestESTAT(AgencyTest):
    agency_id = 'ESTAT'


class TestIMF(AgencyTest):
    agency_id = 'IMF_SDMXCENTRAL'


class TestINSEE(AgencyTest):
    agency_id = 'INSEE'


@pytest.mark.xfail(reason='400 errors; JSON endpoints not correctly handled in'
                          ' api.Request')
class TestOECD(AgencyTest):
    agency_id = 'OECD'


class TestSGR(AgencyTest):
    agency_id = 'SGR'


class TestUNESCO(AgencyTest):
    agency_id = 'UNESCO'


class TestUNSD(AgencyTest):
    # FIXME
    # - http://data.un.org/WS/rest/datastructure/UNSD
    #   /latest?references=parentsandsiblings : raises ParseError: <Concept:
    #  'FREQ'=''> not located in <ConceptScheme: 'MDG_DATA_CONCEPTS', 0 items>
    agency_id = 'UNSD'


class TestWB(AgencyTest):
    agency_id = 'WBG_WITS'
