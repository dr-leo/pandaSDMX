import importlib
from distutils import version
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from .data import BASE_PATH


def assert_pd_equal(left, right, **kwargs):
    """Assert equality of two pandas objects."""
    if left is None:
        return
    method = {
        pd.Series: pd.testing.assert_series_equal,
        pd.DataFrame: pd.testing.assert_frame_equal,
        np.ndarray: np.testing.assert_array_equal,
    }[left.__class__]
    method(left, right, **kwargs)


class MessageTest:
    path: Path = BASE_PATH
    filename: str

    @pytest.fixture(scope="class")
    def msg(self):
        import sdmx

        return sdmx.read_sdmx(self.path / self.filename)


# thanks to xarray
def _importorskip(modname, minversion=None):
    try:
        mod = importlib.import_module(modname)
        has = True
        if minversion is not None:
            if LooseVersion(mod.__version__) < LooseVersion(minversion):
                raise ImportError("Minimum version not satisfied")
    except ImportError:
        has = False
    func = pytest.mark.skipif(not has, reason="requires {}".format(modname))
    return has, func


def LooseVersion(vstring):
    # When the development version is something like '0.10.9+aac7bfc', this
    # function will just discard the git commit id.
    vstring = vstring.split("+")[0]
    return version.LooseVersion(vstring)


has_requests_cache, requires_requests_cache = _importorskip("requests_cache")
