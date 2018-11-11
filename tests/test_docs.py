"""Test code appearing in the documentation.

The 'remote_data' mark, from the pytest plugin 'pytest-remotedata', is used to
mark tests that will access the Internet. In order to run these tests, a
command-line argument must be given:

$ py.test --remote-data [...]

"""
import pytest

import pandas as pd
import pandasdmx
from pandasdmx import Request

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
@pytest.mark.xfail(reason='api.Request._make_key_from_dsd() needs refactor')
def test_doc_index2():
    """Second code example in index.rst."""
    estat = Request('ESTAT')

    resp = estat.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
                      params={'startPeriod': '2007'})

    # We use a generator expression to select some columns
    # and write them to a pandas DataFrame
    data = resp.write(s for s in resp.data.series if s.key.AGE == 'TOTAL')

    # Explore the data set. First, show dimension names
    data.columns.names

    # and corresponding dimension values
    data.columns.levels

    # Show aggregate unemployment rates across ages and sexes as
    # percentage of active population
    data.loc[:, ('PC_ACT', 'TOTAL', 'T')]


@pytest.mark.remote_data
def test_usage_1():
    """Code examples in usage.rst."""
    from pandasdmx import Request

    ecb = Request('ECB')

    ecb_via_proxy = Request('ECB', proxies={'http': 'http://1.2.3.4:5678'})

    ecb_via_proxy.client.config

    cat_response = ecb.categoryscheme()

    cat_response.url

    cat_response.http_headers

    cat_response.write().categoryscheme

    list(cat_response.categoryscheme.MOBILE_NAVI['07'])

    cat_response.write().dataflow.head()

    flows = ecb.dataflow()

    dsd_id = cat_response.dataflow.EXR.structure.id
    dsd_id
    refs = dict(references='all')
    dsd_response = ecb.datastructure(resource_id=dsd_id, params=refs)
    dsd = dsd_response.datastructure[dsd_id]

    dsd.dimensions.aslist()
    dsd_response.write().codelist.loc['CURRENCY'].head()

    data_response = ecb.data(resource_id='EXR', key={'CURRENCY': 'USD+JPY'},
                             params={'startPeriod': '2016'})
    data = data_response.data
    type(data)

    data.dim_at_obs
    series_l = list(data.series)
    len(series_l)
    series_l[5].key
    set(s.key.FREQ for s in data.series)

    daily = (s for s in data.series if s.key.FREQ == 'D')
    cur_df = data_response.write(daily)
    cur_df.shape
    cur_df.tail()
