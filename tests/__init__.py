import importlib
from pathlib import Path
from distutils import version

import pytest

test_data_path = Path(__file__).parent / 'data'

# List of specimen files. Each is a tuple: (path, xml|json, data|structure)
_test_files = []

# XML data files
for part in 'ng', 'rg', 'sg':
    path = test_data_path / 'exr' / 'ecb_exr_{}'.format(part) / 'generic'
    _test_files.extend((p, 'xml', 'data') for p in path.iterdir())

# XML structure files
_test_files.extend(
    (test_data_path.joinpath(*parts), 'xml', 'structure') for parts in [
        ('common', 'common.xml'),
        ('estat', 'apro_dsd.xml'),
        ('insee', 'insee-bug-data-namedtuple-datastructure.xml'),
        ('insee', 'insee-dataflow.xml'),
        ('insee', 'insee-IPI-2010-A21-datastructure.xml'),
        ])

# JSON data files
for fp in (test_data_path / 'json').iterdir():
    _test_files.append((fp, 'json', 'data'))


def test_files(format=None, kind=None):
    """Generate a sequence of test file paths matching criteria."""
    result = []
    for path, f, k in _test_files:
        if (format and format != f) or (kind and kind != k):
            continue
        result.append(path)
    return result


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
    # Our development version is something like '0.10.9+aac7bfc'
    # This function just ignored the git commit id.
    vstring = vstring.split('+')[0]
    return version.LooseVersion(vstring)


has_requests_cache, requires_requests_cache = _importorskip('requests_cache')
