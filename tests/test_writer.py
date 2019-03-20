"""Tests for pandasdmx/writer.py."""
# TODO test all possible values of Writer.write() arguments
# - asframe
# - attribute
# - fromfreq
# - parsetime
# …for each type of input argument.

import pandas as pd
import pytest
from pytest import raises

import pandasdmx
from pandasdmx.writer import Writer

from . import (
    assert_pd_equal,
    expected_data,
    test_data_path,
    test_files,
    specimen,
    )


# file name → (exception raised, exception message, comment/reason)
file_marks = {
    'exr-action-delete.json': (
        AssertionError,
        "Expected type <class 'pandas.core.frame.DataFrame'>, found <class "
        " 'list'> instead",
        'Message contains two DataSets; test infrastructure currently handles '
        'only messages with a single DataSet.'),
    }


def pytest_generate_tests(metafunc):
    if 'data_path' in metafunc.fixturenames:
        params = []
        tf = test_files(kind='data')
        for value, id in zip(tf['argvalues'], tf['ids']):
            try:
                mark = pytest.mark.skip(file_marks[id][2])
                kwarg = dict(marks=mark)
            except KeyError:
                kwarg = {}
            params.append(pytest.param(value, id=id, **kwarg))

        metafunc.parametrize('data_path', params)


def test_write_data_arguments():
    msg = pandasdmx.open_file(test_files(kind='data')['argvalues'][0])

    # Attributes must be a string
    with raises(TypeError):
        Writer().write(msg, attributes=2)

    # Attributes must contain only 'dgso'
    with raises(ValueError):
        Writer().write(msg, attributes='foobarbaz')


def test_write_data(data_path):
    msg = pandasdmx.open_file(data_path)

    result = Writer().write(msg)

    expected = expected_data(data_path)
    if expected is not None:
        print(expected, result, sep='\n')
    assert_pd_equal(expected, result)

    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)


@pytest.mark.parametrize('path', **test_files(kind='data'))
def test_write_data_attributes(path):
    msg = pandasdmx.open_file(path)

    result = Writer().write(msg, attributes='osgd')
    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)


def test_write_agencyscheme():
    # Convert an agency scheme
    with specimen('ecb_orgscheme.xml') as f:
        msg = pandasdmx.open_file(f)
        data = pandasdmx.to_pandas(msg)

    assert data['organisation_scheme']['AGENCIES']['ESTAT'] == 'Eurostat'


def test_write_categoryscheme():
    with specimen('insee-IPI-2010-A21-datastructure.xml') as f:
        msg = pandasdmx.open_file(f)
        print(msg.category_scheme)
        data = pandasdmx.to_pandas(msg)

    cs = data['category_scheme']['CLASSEMENT_DATAFLOWS']

    assert (cs.loc['COMPTA-NAT', 'name']
            == 'National accounts (GDP, consumption...)')

    # Children appear
    assert cs.loc['CNA-PIB-2005', 'parent'] == 'CNA-PIB'


def test_write_codelist():
    # Retrieve codelists from a test specimen and convert to pandas
    dsd_common = pandasdmx.open_file(test_data_path / 'common' / 'common.xml')
    codelists = pandasdmx.to_pandas(dsd_common)['codelist']

    # File contains 5 code lists
    assert len(codelists) == 5

    # Code lists have expected number of items
    assert len(codelists['CL_FREQ']) == 8

    # Items names can be retrieved by ID
    freq = codelists['CL_FREQ']
    assert freq['A'] == 'Annual'

    # Non-hierarchical code list has a string name
    assert freq.name == 'Code list for Frequency (FREQ)'

    # Hierarchical code list
    with specimen('unsd_codelist_partial.xml') as f:
        msg = pandasdmx.open_file(f)

    # Convert single codelist
    CL_AREA = pandasdmx.to_pandas(msg.codelist['CL_AREA'])

    # Hierichical list has a 'parent' column; parent of Africa is the World
    assert CL_AREA.loc['002', 'parent'] == '001'

    # Pandas features can be used to merge parent names
    area_hierarchy = pd.merge(CL_AREA, CL_AREA,
                              how='left', left_on='parent', right_index=True,
                              suffixes=('', '_parent'))
    assert area_hierarchy.loc['002', 'name_parent'] == 'World'


def test_write_conceptscheme():
    with specimen('common.xml') as f:
        msg = pandasdmx.open_file(f)
        data = pandasdmx.to_pandas(msg)

    cdc = data['concept_scheme']['CROSS_DOMAIN_CONCEPTS']
    assert cdc.loc['UNIT_MEASURE', 'name'] == 'Unit of Measure'


@pytest.mark.xfail(reason='TODO: iterable of DataflowDefinition not converted'
                          'to pd.Series')
def test_write_dataflow():
    # Read the INSEE dataflow definition
    with specimen('insee-dataflow') as f:
        msg = pandasdmx.open_file(f)

    # Convert to pandas
    result = pandasdmx.to_pandas(msg)

    assert len(result['dataflow']) == 663
    assert isinstance(result['dataflow'], pd.Series)


@pytest.mark.parametrize('path', **test_files(kind='structure'))
def test_writer_structure(path):
    msg = pandasdmx.open_file(path)

    pandasdmx.to_pandas(msg)

    # TODO test contents
