How to…
=======

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
