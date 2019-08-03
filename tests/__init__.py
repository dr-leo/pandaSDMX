from contextlib import contextmanager
import importlib
import json
from pathlib import Path
from distutils import version

import numpy as np
import pandas as pd
import pytest

test_data_path = Path(__file__).parent / 'data'

# List of specimen files. Each is a tuple: (path, xml|json, data|structure)
_test_files = []

# XML data files
for part in 'ng', 'rg', 'sg':
    for struct in 'generic', 'structured':
        path = test_data_path / 'exr' / 'ecb_exr_{}'.format(part) / struct
        _test_files.extend((p, 'xml', 'data') for p in path.iterdir())

# XML structure files
_test_files.extend(
    (test_data_path.joinpath(*parts), 'xml', 'structure') for parts in [
        ('common', 'common.xml'),
        ('common', 'ecb_orgscheme.xml'),
        ('common', 'unsd_codelist_partial.xml'),
        ('estat', 'apro_dsd.xml'),
        ('insee', 'insee-bug-data-namedtuple-datastructure.xml'),
        ('insee', 'insee-dataflow.xml'),
        ('insee', 'insee-IPI-2010-A21-datastructure.xml'),
        ])

# JSON data files
for fp in (test_data_path / 'json').iterdir():
    _test_files.append((fp, 'json', 'data'))


def test_files(format=None, kind=None):
    """Generate a sequence of test file paths matching criteria.

    The return value should be passed as kwargs to pytest.mark.parametrize():

        pytest.mark.parametrize('argname', **test_files(…))

    """
    result = dict(argvalues=[], ids=[])
    for path, f, k in _test_files:
        if (format and format != f) or (kind and kind != k):
            continue
        result['argvalues'].append(path)
        result['ids'].append(path.name)
    return result


@contextmanager
def specimen(pattern='', opened=True):
    """Open the test specimen file with *match* in the name."""
    for path, f, k in _test_files:
        if path.match('*' + pattern + '*'):
            # str() here is for Python 3.5 compatibility
            yield open(str(path)) if opened else path
            break


# str() here is for Python 3.5 compatibility
_expected_read_args = json.load(open(str(test_data_path / 'expected.json')))


def expected_data(path):
    """Return the expected write() results for *path*."""
    args = dict(sep=r'\s+', index_col=[0], header=[0])
    try:
        args.update(_expected_read_args[path.name])
        expected_path = (test_data_path / 'expected' /
                         path.name).with_suffix('.txt')
        result = pd.read_csv(expected_path, **args)

        # A series; unwrap
        if set(result.columns) == {'value'}:
            result = result['value']

        return result
    except KeyError:
        return None


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
    path = test_data_path
    filename = None

    @pytest.fixture(scope='class')
    def msg(self):
        import pandasdmx as sdmx
        return sdmx.read_sdmx(self.path / self.filename)


# thanks to xarray
def _importorskip(modname, minversion=None):
    try:
        mod = importlib.import_module(modname)
        has = True
        if minversion is not None:
            if LooseVersion(mod.__version__) < LooseVersion(minversion):
                raise ImportError('Minimum version not satisfied')
    except ImportError:
        has = False
    func = pytest.mark.skipif(not has, reason='requires {}'.format(modname))
    return has, func


def LooseVersion(vstring):
    # When the development version is something like '0.10.9+aac7bfc', this
    # function will just discard the git commit id.
    vstring = vstring.split('+')[0]
    return version.LooseVersion(vstring)


has_requests_cache, requires_requests_cache = _importorskip('requests_cache')
