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
from pandasdmx.writer.data2pandas import Writer

from . import assert_pd_equal, expected_data, test_files


def test_write_arguments(req):
    msg = pandasdmx.open_file(test_files(kind='data')['argvalues'][0])

    # Attributes must be a string
    with raises(TypeError):
        Writer(msg).write(msg, attributes=2)

    # Attributes must contain only 'dgso'
    with raises(ValueError):
        Writer(msg).write(msg, attributes='foobarbaz')


@pytest.mark.parametrize('path', **test_files(kind='data'))
def test_write(path):
    msg = pandasdmx.open_file(path)

    result = Writer(msg).write(msg)

    expected = expected_data(path)
    if expected is not None:
        print(expected, result, sep='\n')
    assert_pd_equal(expected, result)

    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)


@pytest.mark.parametrize('path', **test_files(kind='data'))
def test_write_attributes(path):
    msg = pandasdmx.open_file(path)

    result = Writer(msg).write(msg, attributes='osgd')
    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)
