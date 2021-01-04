Development roadmap
===================

This page describes some possible future enhancements to pandaSDMX. Contributions are welcome!


Make the pandas writer more user-friendly
-----------------------------------------

The writer returns pd.Series objects by default. While this is a sensible approach as it works in most situations,
users may find dataframes with datetime or period indices more useful. To this end,
the writer (or the :func:`~pandasdmx.to_pandas` function wrapping it)
accept a `datetime`kwarg. See the Howto section for details. 
Having pandaSDMX apply heuristics to retrieve the `TIME` and `FREQ` dimensions
could make it  easier to have the writer return a period-indexed dataframe.

In addition, the writer could extract data-types from a provided DSD and map them to numpy types. Currently, `NP.float64` is used for data values by default.
This is fit for purpose in most cases. But data providers may specify other data types such as int, decimal or categorical. These could be translated to pandas types automatically.

SDMX-JSON
-------------

The SDMX-JSON reader could be extended to support the new
JSON-based structure message representation. Currently, only data messages are supported.


Optimize parsing
----------------

The current readers implement depth-first parsing of XML or JSON SDMX messages.
This ensures the returned objects confirm rigorously to the SDMX Information Model, but can be slow for very large messages (both Structure and Data).

There are some ways this performance could be improved:

- Create-on-access (as in v0.9): don't immediately parse an entire document, but only as requested to construct other objects.
  This would make some internals more complex:

  - Observation association with GroupKeys is determined by comparing the Observation key with the GroupKey.
    In order to have a complete list of all Observations associated with a GroupKey, at least the dimension of each Observation would need to be parsed immediately.

  - In pandasdmx.sdmxml.reader, references are determined to be internal or external by checking against an _index of already-parsed objects.
    This index would need to represent existing-but-not-parsed objects.

- Parallelize parsing, e.g. at the level of Series or other mostly-separate collections of objects.

SDMX features & miscellaneous
-----------------------------

- pandasdmx.api.Request._resources only contains a small subset of: https://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1 (see "NOT SUPPORTED OPERATIONS"); provide the rest.

- re-add support for cascading content constraints. This features  was present in v0.9, but dropped in v1.0 as no consensus could be reached.

- Use the `XML Schema <https://en.wikipedia.org/wiki/XML_Schema_(W3C)>`_ definitions of SDMX-ML to validate messages and snippets.

- SOAP APIs. Currently only REST APIs are supported.
  This would allow access to, e.g., a broader set of :ref:`IMF` data.

- Performance.
  Parsing some messages can be slow.
  Install pytest-profiling_ and run, for instance::

      $ py.test --profile --profile-svg -k xml_structure_insee
      $ python3 -m pstats prof/combined.prof
      % sort cumulative
      % stats

Inline TODOs
~~~~~~~~~~~~

.. todolist::

.. _pytest-profiling: https://pypi.org/project/pytest-profiling/
