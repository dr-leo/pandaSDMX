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

Convert dimensions to :class:`pandas.DatetimeIndex` or :class:`~pandas.PeriodIndex`
-----------------------------------------------------------------------------------

SDMX datasets often have a :class:`~.Dimension` with a name like ``TIME_PERIOD``.
To ease further processing of time-series data read from SDMX messages, :func:`.write_dataset` provides a `datetime` argument to convert these into :class:`pandas.DatetimeIndex` and :class:`~pandas.PeriodIndex` classes.

For multi-dimensional datasets, :func:`~.write_dataset` usually returns a :class:`pandas.Series` with a :class:`~pandas.MultiIndex` that has one level for each dimension.
However, MultiIndex and DatetimeIndex/PeriodIndex are incompatible; it is not possible to use pandas' date/time features for *just one level* of a MultiIndex (e.g. ``TIME_PERIOD``) while using other types for the other levels/dimensions (e.g. strings for ``CURRENCY``).

For this reason, when the `datetime` argument is used, :func:`~.write_dataset` returns a :class:`~pandas.DataFrame`: the DatetimeIndex/PeriodIndex is used along axis 0, and *all other dimensions* are collected in a MultiIndex on axis 1.

An example, using the same European Central Bank exchange rate data set as in the :doc:`walkthrough <walkthrough>`:

.. ipython:: python

   import pandasdmx as sdmx
   ecb = sdmx.Request('ECB')
   data_msg = ecb.data(
       'EXR',
       key=dict(CURRENCY_DENOM='EUR', FREQ='M', EXR_SUFFIX='A'),
       params=dict(startPeriod='2019-01', endPeriod='2019-06'),
   )
   data = data_msg.data[0]

Without date-time conversion, :meth:`~.to_pandas` produces a MultiIndex:

.. ipython:: python

   sdmx.to_pandas(data)

With date-time conversion, it produces a DatetimeIndex:

.. ipython:: python

   df1 = sdmx.to_pandas(data, datetime='TIME_PERIOD')
   df1.index
   df1

Use the advanced functionality to specify a dimension for the frequency of a PeriodIndex, and change the orientation so that the PeriodIndex is on the columns:

.. ipython:: python

   df2 = sdmx.to_pandas(
     data,
     datetime=dict(dim='TIME_PERIOD', freq='FREQ', axis=1))
   df2.columns
   df2

.. warning:: For large datasets, parsing datetimes may reduce performance.


.. _howto-references:

Use the 'references' query parameter
------------------------------------

SDMX web services support a ``references`` parameter in HTTP requests which can take values such as 'all', 'descendants', etc.
This parameter instructs the web service to include, when generating a Data- or StructureMessage, the objects implicitly designated by the ``references`` parameter alongside the explicit resource.
For example, for the request:

>>> response = some_agency.dataflow('SOME_ID', params={'references': 'all'})

the response will include:

- the dataflow 'SOME_ID' explicitly specified,
- the DSD referenced by the dataflow's ``structure`` attribute,
- the code lists referenced by the DSD, and
- any content-constraints which reference the dataflow or the DSD.

It is much more efficient to request many objects in a single request.
Thus, pandaSDMX provides default values for ``references`` in common queries.
For instance, when a single dataflow is requested by specifying its ID, pandaSDMX sets ``references`` to 'all'.
On the other hand, when the dataflow ID is wildcarded, it is more practical not to request all referenced objects alongside as the response would likely be excessively large, and the user is deemed to be interested in the bird's eye perspective (list of dataflows) prior to focusing on a particular dataflow and its descendents and ancestors.
The default value for the ``references`` parameter can be overridden.

Some web services differ in how they handle ``references``—for instance, :ref:`ESTAT <ESTAT>`.
See :doc:`sources` for details.


.. _howto-categoryscheme:

Use category schemes to explore data
------------------------------------

SDMX supports category-schemes to categorize dataflow definitions and other objects.
This helps retrieve, e.g., a dataflow of interest. Note that not all agencies support categoryschemes.
A good example is the ECB.
However, as the ECB's SDMX service offers less than 100 dataflows, using categoryschemes is not strictly necessary.
A counter-example is Eurostat which offers more than 6000 dataflows, yet does not categorize them.
Hence, the user must search through the flat list of dataflows.

To search the list of dataflows by category, we request the category scheme from the ECB's SDMX service and explore the response:

.. ipython:: python

    import pandasdmx as sdmx
    ecb = sdmx.Request('ecb')
    cat_response = ecb.categoryscheme()

Like any other scheme, a category scheme is essentially a dict mapping ID's to the actual SDMX objects.
To display the categorised items, in our case the dataflow definitions contained in the category on exchange rates, we iterate over the `Category` instance:

.. ipython:: python

    sdmx.to_pandas(cat_response.category_scheme.MOBILE_NAVI)
    cat_response.category_scheme.MOBILE_NAVI

.. versionadded:: 0.5


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
