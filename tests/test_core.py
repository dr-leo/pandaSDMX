"""Test __init__.py"""
import pytest

import pandasdmx


@pytest.mark.xfail(reason='https://github.com/blaze/odo/issues/621',
                   raises=AttributeError, strict=True)
def test_odo_register():
    pandasdmx.odo_register()
