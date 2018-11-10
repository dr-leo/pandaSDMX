"""Tests for pandasdmx/writer/data2pandas.py."""
# TODO test all possible values of Writer.write() arguments
# - asframe
# - attribute
# - fromfreq
# - parsetime
# …for each type of input argument.

import pytest
from pytest import raises

from pandasdmx.writer.data2pandas import Writer

from . import test_data_path


# test_data_path = test_data_path / 'exr' / 'ecb_exr_ng' / 'generic'
test_data_path = test_data_path / 'json'

test_data = list(test_data_path.iterdir())


def test_write_arguments(req):
    msg = req.get(fromfile=test_data[0]).msg

    # Attributes must be a string
    with raises(TypeError):
        Writer(msg).write(msg, attributes=2)

    # Attributes must contain only 'dgso'
    with raises(ValueError):
        Writer(msg).write(msg, attributes='foobarbaz')


@pytest.mark.parametrize('path', test_data)
def test_write_json(req, path):
    msg = req.get(fromfile=path).msg

    Writer(msg).write(msg)


@pytest.mark.parametrize('path', test_data)
def test_write_json_attributes(req, path):
    msg = req.get(fromfile=path).msg

    Writer(msg).write(msg, attributes='osgd')
