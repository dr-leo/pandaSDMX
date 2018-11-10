"""Test code appearing in the documentation.

The 'remote_data' mark, from the pytest plugin 'pytest-remotedata', is used to
mark tests that will access the Internet. In order to run these tests, a
command-line argument must be given:

$ py.test --remote-data [...]

"""
import pytest

from pandasdmx import Request


@pytest.mark.remote_data
def test_doc_index1():
    """First code box in index.rst."""
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

    pytest.xfail('writer.structure2pd needs refactor')
    # Show some codelists
    structure_response.write().codelist.loc['GEO'].head()


@pytest.mark.remote_data
@pytest.mark.xfail(reason='api.Request._make_key_from_dsd() needs refactor')
def test_doc_index2():
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
