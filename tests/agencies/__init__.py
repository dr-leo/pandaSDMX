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
