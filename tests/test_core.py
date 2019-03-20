"""Test __init__.py"""
import pytest

import pandasdmx


@pytest.mark.xfail('https://github.com/blaze/odo/issues/621',
                   raises=AttributeError)
def test_odo_register():
    pandasdmx.odo_register()
