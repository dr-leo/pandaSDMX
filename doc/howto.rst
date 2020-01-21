How to…
=======

.. contents::
   :local:
   :backlinks: none

Access other SDMX data sources
------------------------------

:mod:`pandaSDMX` ships with a file, `sources.json`, that includes information about the capabilities of many :doc:`data sources <sources>`.
However, any data source that generates SDMX 2.1 messages is supported.
There are multiple ways to access these:

1. Create a :class:`pandasdmx.Request` without a named data source, then call the :meth:`~.Request.get` method using the `url` argument::

    import pandasdmx as sdmx
    req = sdmx.Request()
    req.get(url='https://sdmx.example.org/path/to/webservice', ...)

2. Call :meth:`~pandasdmx.source.add_source` with a JSON snippet describing the data provider.

3. Create a subclass of :class:`~pandasdmx.source.Source`, providing attribute values and optional implementations of hooks.


.. _howto-datetime:

Convert dimensions to :class:`pandas.DatetimeIndex` or :class:`pandas.PeriodIndex`
----------------------------------------------------------------------------------

SDMX datasets often have a :class:`~.Dimension` with a name like ``TIME_PERIOD``.
To ease further processing of time-series data read from SDMX messages, :func:`.write_dataset` provides a `datetime` argument to convert these into :class:`pandas.DatetimeIndex` and :class:`~pandas.PeriodIndex` classes.

For multi-dimensional datasets, :func:`~.write_dataset` usually returns a :class:`pandas.Series` with a :class:`~pandas.MultiIndex` that has one level for each dimension.
However, MultiIndex and DatetimeIndex/PeriodIndex are incompatible; it is not possible to use pandas' date/time features for *just one level* of a MultiIndex (e.g. ``TIME_PERIOD``) while using other types for the other levels/dimensions (e.g. strings for ``CURRENCY``).

For this reason, when the `datetime` argument is used, :func:`~.write_dataset` returns a :class:`~pandas.DataFrame`: the DatetimeIndex/PeriodIndex is used along axis 0, and *all other dimensions* are collected in a MultiIndex on axis 1.

An example, using the same European Central Bank exchange rate data set as in the :doc:`walkthrough <walkthrough>`:

.. ipython:: python

   import pandasdmx as sdmx
   ecb = sdmx.Request('ECB')
   data_msg = ecb.data('EXR', key={'CURRENCY': ['EUR']},
                        params={'startPeriod': '2019'})
   data = data_msg.data[0]

Without date-time conversion, :meth:`~.to_pandas` produces a MultiIndex:

.. ipython:: python

   sdmx.to_pandas(data)

With date-time conversion, it produces a DatetimeIndex:

.. ipython:: python

   df1 = sdmx.to_pandas(data, datetime='TIME_PERIOD')
   df1.index
   df1

Using the advanced functionality to specify a dimension for the frequency of a PeriodIndex, and change the orientation so that the PeriodIndex is on the columns:

.. ipython:: python

   df2 = sdmx.to_pandas(
     data,
     datetime=dict(dim='TIME_PERIOD', freq='FREQ', axis=1))
   df2.columns
   df2

.. warning:: For large datasets, parsing datetimes may reduce performance.


.. _howto-convert:

Convert SDMX data to other formats
----------------------------------

Pandas supports output to `many popular file formats <http://pandas.pydata.org/pandas-docs/stable/user_guide/io.html>`_.
Call these methods on the objects returned by :meth:`~pandasdmx.to_pandas`.
For instance::

    msg = sdmx.read_sdmx('data.xml')
    sdmx.to_pandas(msg).to_excel('data.xlsx')


pandaSDMX can also be used with `odo <https://github.com/blaze/odo>`_ by registering methods for discovery and conversion::

    import odo
    from odo.utils import keywords
    import pandas as pd
    from toolz import keyfilter
    import toolz.curried.operator as op

    class PandaSDMX(object):
        def __init__(self, uri):
            self.uri = uri

    @odo.resource.register(r'.*\.sdmx')
    def _resource(uri, **kwargs):
        return PandaSDMX(uri)

    @odo.discover.register(PandaSDMX)
    def _discover(obj):
        return odo.discover(sdmx.to_pandas(sdmx.read_sdmx(obj.uri)))

    @odo.convert.register(pd.DataFrame, PandaSDMX)
    def _convert(obj, **kwargs):
        msg = sdmx.read_sdmx(obj.uri)
        return sdxm.to_pandas(msg, **keyfilter(op.contains(keywords(write)),
                                               kwargs))

.. deprecated:: 1.0

   odo `appears unmaintained <https://github.com/blaze/odo/issues/619>`_ since about 2016, so pandaSDMX no longer provides built-in registration.

.. versionadded:: 0.4

   :meth:`pandasdmx.odo_register` was added, providing automatic registration.
