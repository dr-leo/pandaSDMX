"""Tests for pandasdmx/writer/data2pandas.py."""
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

from . import assert_pd_equal, expected_data, test_data_path, test_files


xfail = {
    'ecb_exr_ng_xs.xml': (AssertionError, "Series length are different"),
    'exr-action-delete.json': (AssertionError, """Expected type <class
        'pandas.core.frame.DataFrame'>, found <class 'list'> instead"""),
    'exr-cross-section.json': (AssertionError, """Expected type <class
        'pandas.core.frame.DataFrame'>, found <class
        'pandas.core.series.Series'> instead"""),
    'exr-time-series.json': (AssertionError, """Expected type <class
        'pandas.core.frame.DataFrame'>, found <class
        'pandas.core.series.Series'> instead"""),
    }


def pytest_generate_tests(metafunc):
    if 'data_path' in metafunc.fixturenames:
        params = []
        tf = test_files(kind='data')
        for value, id in zip(tf['argvalues'], tf['ids']):
            try:
                mark = pytest.mark.xfail(strict=True, raises=xfail[id][0])
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


def test_write_dsd_common():
    dsd_common = pandasdmx.open_file(test_data_path / 'common' / 'common.xml')
    Writer().write(dsd_common)


@pytest.mark.parametrize('path', **test_files(kind='structure'))
def test_writer_structure(path):
    msg = pandasdmx.open_file(path)
    Writer().write(msg)
