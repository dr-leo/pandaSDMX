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

from . import test_files


def test_write_arguments(req):
    msg = req.get(fromfile=next(test_files(kind='data'))).msg

    # Attributes must be a string
    with raises(TypeError):
        Writer(msg).write(msg, attributes=2)

    # Attributes must contain only 'dgso'
    with raises(ValueError):
        Writer(msg).write(msg, attributes='foobarbaz')


@pytest.mark.parametrize('path', test_files(kind='data'))
def test_write_json(req, path):
    msg = req.get(fromfile=path).msg

    result = Writer(msg).write(msg)
    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame)), type(result)


@pytest.mark.parametrize('path', test_files(kind='data'))
def test_write_json_attributes(req, path):
    msg = req.get(fromfile=path).msg

    result = Writer(msg).write(msg, attributes='osgd')
    # TODO incomplete
    assert isinstance(result, (pd.Series, pd.DataFrame)), type(result)
