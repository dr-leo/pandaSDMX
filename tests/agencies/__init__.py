import pytest

from pandasdmx.api import Request

endpoints = [
    'codelist',
    'dataflow',
    ]


class AgencyTest:
    """Fixture for agency tests."""
    agency_id = None

    @pytest.fixture
    def req(self):
        return Request(self.agency_id)

    @pytest.mark.remote_data
    @pytest.mark.parametrize('endpoint', endpoints)
    def test_common_endpoints(self, req, endpoint):
        req.get(endpoint)
