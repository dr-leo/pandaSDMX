"""Test __init__.py"""
import pytest

import pandasdmx


@pytest.mark.filterwarnings('ignore:pandas.tslib')
def test_odo_register():
    pandasdmx.odo_register()
