# FIXME
# - test_common_endpoints(endpoint='codelist') has an XML tag
#  'AnnotationTitle' not currently handled by reader.sdmxml

from . import AgencyTest


class TestUNSD(AgencyTest):
    agency_id = 'UNSD'
