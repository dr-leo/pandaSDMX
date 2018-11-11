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


@pytest.fixture
def dsd_common():
    return pandasdmx.open_file(test_data_path / 'common' / 'common.xml')


def test_write_data_arguments():
    msg = pandasdmx.open_file(test_files(kind='data')['argvalues'][0])

    # Attributes must be a string
    with raises(TypeError):
        Writer().write(msg, attributes=2)

    # Attributes must contain only 'dgso'
    with raises(ValueError):
        Writer().write(msg, attributes='foobarbaz')


@pytest.mark.parametrize('path', **test_files(kind='data'))
def test_write_data(path):
    msg = pandasdmx.open_file(path)

    result = Writer().write(msg)

    expected = expected_data(path)
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


def test_write_dsd_common(dsd_common):
    Writer().write(dsd_common)


@pytest.mark.parametrize('path', **test_files(kind='structure'))
def test_writer_structure(path):
    msg = pandasdmx.open_file(path)
    Writer().write(msg)
