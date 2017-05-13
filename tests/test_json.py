from collections import OrderedDict
import json
import os
from os.path import abspath, dirname, join
from unittest import TestCase

import pandas as pd
from pandasdmx import Request


# Construct the expected pandas representation of the sample data files
sample_attrs = OrderedDict([
    ('FREQ', 'D'),
    ('CURRENCY_DENOM', 'EUR'),
    ('EXR_TYPE', 'SP00'),
    ('EXR_SUFFIX', 'A'),
    ])


def _idx(name, at_level=None, type=None):
    """Return an index for dimension *name* in the sample data files.

    If *at_level* is an integer, the contents of sample_attrs are added as
    pd.MultiIndex level, with *name* in the position indicated by *at_level*.

    If *name* is 'TIME_PERIOD' and *type* is pd.Period, a pd.PeriodIndex is
    returned.
    """
    cls = pd.Index
    kwargs = dict(name=name)

    if name == 'CURRENCY':
        data = ['NZD', 'RUB']
    elif name == 'TIME_PERIOD':
        data = ['2013-01-18', '2013-01-21']
        if type == pd.Period:
            cls = pd.PeriodIndex
            kwargs['freq'] = 'D'

    idx = cls(data, **kwargs)

    if at_level is not None:
        # Add sample_attrs as extra pd.MultiIndex levels on df.columns
        names = list(sample_attrs.keys())
        iterables = [[v] for v in sample_attrs.values()]
        names.insert(at_level, name)
        iterables.insert(at_level, idx)
        return pd.MultiIndex.from_product(iterables, names=names)
    else:
        return idx


sample_data = {
    'action-delete': pd.DataFrame(
        [[40.3426, 40.3000]],
        index=_idx('CURRENCY')[1:],
        columns=_idx('TIME_PERIOD', 1),
        ),
    'cross-section': pd.DataFrame(
        [[1.5931, 1.5925], [40.3426, 40.3000]],
        index=_idx('CURRENCY'),
        columns=_idx('TIME_PERIOD', 1),
        ),
    'flat': pd.Series(
        [1.5931, 1.5925, 40.3426, 40.3000],
        index=pd.MultiIndex.from_product([[sample_attrs['FREQ']],
                                          _idx('CURRENCY'),
                                          [sample_attrs['CURRENCY_DENOM']],
                                          [sample_attrs['EXR_TYPE']],
                                          [sample_attrs['EXR_SUFFIX']],
                                          _idx('TIME_PERIOD'),
                                          ]),
        ),
    'time-series': pd.DataFrame(
        [[1.5931, 40.3426], [1.5925, 40.3000]],
        index=_idx('TIME_PERIOD', None, pd.Period),
        columns=_idx('CURRENCY', 1),
        ),
    }


class TestJSON(TestCase):

    def setUp(self):
        self.data_path = join(dirname(abspath(__file__)), 'data', 'json')

    def _filepath(self, part):
        return join(self.data_path, 'exr-%s.json' % part)

    def test_samples_request(self):
        """Test the samples from the SDMXJSON spec."""
        req = Request()
        for name, data in sample_data.items():
            resp = req.get(fromfile=self._filepath(name))

            df = resp.write()
            assert df.equals(data), \
                '\n'.join(map(str, [name, df.index, data.index,
                                    getattr(df, 'columns', ''),
                                    getattr(data, 'columns', '')]))

    def test_read_as_str(self):
        """Test the read_as_str() method."""
        resp = Request().get(fromfile=self._filepath('flat'))
        assert resp.header.id == '62b5f19d-f1c9-495d-8446-a3661ed24753'

    def test_write_source(self):
        """Test the write_source() method."""
        req = Request()
        for name in sample_data.keys():
            orig_fn = self._filepath(name)
            temp_fn = self._filepath(name + '-write-source')

            # Read the message
            resp = req.get(fromfile=orig_fn)

            # Write to a temporary JSON file
            resp.write_source(temp_fn)

            # Read the two files and compare JSON (ignores ordering)
            with open(orig_fn) as orig, open(temp_fn) as temp:
                assert json.load(orig) == json.load(temp)

            # Delete the temporary file
            os.remove(temp_fn)
