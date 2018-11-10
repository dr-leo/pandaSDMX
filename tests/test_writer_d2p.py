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

from pandasdmx.writer.data2pandas import Writer

from . import assert_pd_equal, expected_data, test_files


def test_write_arguments(req):
    msg = req.get(fromfile=test_files(kind='data')['argvalues'][0]).msg

    # Attributes must be a string
    with raises(TypeError):
        Writer(msg).write(msg, attributes=2)

    # Attributes must contain only 'dgso'
    with raises(ValueError):
        Writer(msg).write(msg, attributes='foobarbaz')


@pytest.mark.parametrize('path', **test_files(kind='data'))
def test_write(req, path):
    msg = req.get(fromfile=path).msg

    result = Writer(msg).write(msg)

    expected = expected_data(path)
    if expected is not None:
        print(expected, result, sep='\n')
    assert_pd_equal(expected, result)

    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)


@pytest.mark.parametrize('path', **test_files(kind='data'))
def test_write_attributes(req, path):
    msg = req.get(fromfile=path).msg

    result = Writer(msg).write(msg, attributes='osgd')
    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame, list)), type(result)
