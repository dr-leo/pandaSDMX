How to…
=======

.. contents::
   :local:
   :backlinks: none

Access other SDMX data providers
--------------------------------

Any data provider that generates SDMX 2.1 messages is supported.
There are multiple ways to access these:

1. Create a :class:`pandasdmx.Request` without a named data source, then
   provide the `url` argument to :meth:`pandasdmx.api.Request.get`::

    import pandasdmx as sdmx
    req = sdmx.Request()
    req.get(url='https://sdmx.example.org/path/to/webservice', ...)

2. Call :meth:`pandasdmx.source.add_source` with a JSON snippet describing the data provider.

3. Create a subclass of :class:`pandasdmx.source.Source`, providing attribute values and optional implementations of hooks.


Speed up :meth:`pandasdmx.to_pandas` for large datasets
-------------------------------------------------------

The main performance hit comes from parsing the time or time period strings. In
case of regular data such as monthly (not trading day!), call the ``write``
method with ``fromfreq``  set to True so that only the first string will be
parsed and the rest inferred from the frequency of the series. Caution: If the
series is stored in the XML document in reverse chronological order, the
``reverse_obs``  argument must be set to True as well to prevent the resulting
dataframe index from extending into a remote future.


.. _howto-convert:

Convert SDMX data to other formats
----------------------------------

`Pandas <https://pandas.pydata.org>`_ supports output to `many popular file formats <http://pandas.pydata.org/pandas-docs/stable/user_guide/io.html>`_.
Call these methods on the :class:`pandas.DataFrame` objects returned by :meth:`pandasdmx.to_pandas`. For instance::

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

.. versionadded:: 0.4

   ``pandasdmx.odo_register()`` added, providing automatic registration.

.. deprecated:: 1.0

   odo `appears unmaintained <https://github.com/blaze/odo/issues/619>`_ since about 2016, so pandaSDMX no longer provides built-in registration.
