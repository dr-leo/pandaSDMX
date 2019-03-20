"""Test code appearing in the documentation.

The 'remote_data' mark, from the pytest plugin 'pytest-remotedata', is used to
mark tests that will access the Internet. In order to run these tests, a
command-line argument must be given:

$ py.test --remote-data [...]

"""
import pytest

import numpy as np
import pandas as pd
import pandasdmx
from pandasdmx import Request
from pandasdmx.model import DataSet

from . import assert_pd_equal


@pytest.mark.remote_data
def test_doc_index1():
    """First code example in index.rst."""
    estat = Request('ESTAT')
    flow_response = estat.dataflow('une_rt_a')

    with pytest.raises(TypeError):
        # This presumes the DataStructureDefinition instance can conduct a
        # network request for its own content
        structure_response = flow_response.dataflow.une_rt_a.structure(
            request=True, target_only=False)

    # Same effect
    structure_response = estat.get(
        'datastructure', flow_response.dataflow.une_rt_a.structure.id)

    # Even better: Request.get(…) should examine the class and ID of the object
    # structure = estat.get(flow_response.dataflow.une_rt_a.structure)

    # Show some codelists
    s = pandasdmx.to_pandas(structure_response)
    expected = pd.Series({
        'AT': 'Austria',
        'BE': 'Belgium',
        'BG': 'Bulgaria',
        'CY': 'Cyprus',
        'CZ': 'Czechia',
        }, name='CL_GEO')

    with pytest.raises(AttributeError):
        # Codelists returned as a single pd.Series with a pd.MultiIndex
        s.codelist.loc['GEO'].head()

    # Same effect
    assert_pd_equal(s.codelist['CL_GEO'].sort_index().head(), expected)


@pytest.mark.remote_data
def test_doc_index2():
    """Second code example in index.rst."""
    estat = Request('ESTAT')

    resp = estat.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
                      params={'startPeriod': '2007', 'endPeriod': '2018'})

    # Convert to a pd.DataFrame and use stock pandas methods on the index to
    # select a subset
    data = pandasdmx.to_pandas(resp.data[0]).xs('TOTAL', level='AGE',
                                                drop_level=False)

    # Explore the data set. First, show dimension names
    data.index.names

    # and corresponding dimension values
    data.index.levels

    # Show aggregate unemployment rates across ages and sexes as
    # percentage of active population
    idx = pd.IndexSlice
    subset = data[idx['PC_ACT', 'TOTAL', 'T']]
    assert len(subset) == 3 * 12  # GEO, TIME_PERIOD


@pytest.mark.remote_data
def test_doc_usage_structure():
    """Code examples in usage.rst."""
    ecb = Request('ECB')

    ecb_via_proxy = Request('ECB', proxies={'http': 'http://1.2.3.4:5678'})

    assert all(getattr(ecb_via_proxy.session, k) == v for k, v in (
        ('proxies', {'http': 'http://1.2.3.4:5678'}),
        ('stream', True),
        ('timeout', 30.1),
        ))

    cat_response = ecb.categoryscheme()

    # FIXME: the documentation shows 'references=all'
    assert cat_response.response.url == ('http://sdw-wsrest.ecb.int/service/'
                                         'categoryscheme/latest?references='
                                         'parentsandsiblings')

    # TODO check specific headers
    cat_response.response.headers

    print(pandasdmx.to_pandas(cat_response.category_scheme))

    # This currently produces an AttributeError in the compiled
    #  documentation: https://pandasdmx.readthedocs.io/en/master/usage.html
    # list(cat_response.category_scheme.MOBILE_NAVI['07'])

    print(pandasdmx.to_pandas(cat_response.dataflow))

    # This step is slow
    # flows = ecb.dataflow()

    # Also raising exceptions in the compiled documentation
    # dsd_id = cat_response.dataflow.EXR.structure.id
    # dsd_id
    # refs = dict(references='all')
    # dsd_response = ecb.datastructure(resource_id=dsd_id, params=refs)
    # dsd = dsd_response.datastructure[dsd_id]

    # dsd.dimensions.aslist()
    # dsd_response.write().codelist.loc['CURRENCY'].head()


@pytest.mark.remote_data
def test_doc_usage_data():
    """Code examples in usage.rst."""
    ecb = Request('ECB')

    data_response = ecb.data(resource_id='EXR', key={'CURRENCY': 'USD+JPY'},
                             params={'startPeriod': '2016',
                                     'endPeriod': '2016-12-31'})
    # # Commented: do the same without triggering requests for validation
    # data_response = ecb.data(resource_id='EXR', key='.JPY+USD...',
    #                          params={'startPeriod': '2016',
    #                                  'endPeriod': '2016-12-31'})
    data = data_response.data[0]

    assert type(data) is DataSet

    # This message doesn't explicitly specify the remaining dimensions; unless
    # they are inferred from the SeriesKeys, then the DimensionDescriptor is
    # not complete
    # assert data.structured_by.dimensions[-1] == 'TIME_PERIOD'
    # data.dim_at_obs

    series_keys = list(data.series)

    assert len(series_keys) == 16

    series_keys[5]

    assert (sorted(set(sk.FREQ.value for sk in data.series))
            == 'A D H M Q'.split())

    daily = pandasdmx.to_pandas(data).xs('D', level='FREQ')
    assert len(daily) == 514

    assert_pd_equal(daily.tail().values,
                    np.array([1.0446, 1.0445, 1.0401, 1.0453, 1.0541]))
