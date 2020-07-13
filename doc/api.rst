API reference
=============

See also the :doc:`implementation`.

.. contents::
   :local:
   :backlinks: none

Top-level methods and classes
-----------------------------
.. automodule:: pandasdmx
   :members:
   :exclude-members: logger

.. autodata:: logger

   By default, messages at the :ref:`log level <py:levels>` ``ERROR`` or
   greater are printed to :obj:`sys.stderr`.
   These include the web service query details (URL and headers) used by :class:`.Request`.

   To debug requests to web services, set to a more permissive level::

       import logging

       pandasdmx.logger.setLevel(logging.DEBUG)

   .. versionadded:: 0.4


``message``: pandasdmx.messages
-------------------------------
.. automodule:: pandasdmx.message
   :members:
   :undoc-members:
   :show-inheritance:

.. _api-model:

``model``: SDMX Information Model
---------------------------------

.. automodule:: pandasdmx.model
   :members:
   :undoc-members:
   :show-inheritance:

``reader``: Parsers for SDMX file formats
-----------------------------------------

SDMX-ML
:::::::

.. currentmodule:: pandasdmx.reader.sdmxml

:mod:`pandasdmx` supports the several types of SDMXML messages.

.. autoclass:: pandasdmx.reader.sdmxml.Reader
    :members:
    :undoc-members:

SDMX-JSON
:::::::::

.. currentmodule:: pandasdmx.reader.sdmxjson

.. autoclass:: pandasdmx.reader.sdmxjson.Reader
    :members:
    :undoc-members:


Reader API
::::::::::

.. currentmodule:: pandasdmx.reader

.. automodule:: pandasdmx.reader
   :members:

.. autoclass:: pandasdmx.reader.base.BaseReader
   :members:


``writer``: Convert ``sdmx`` objects to other formats
-----------------------------------------------------

.. _writer-pandas:

``writer.pandas``: Convert to ``pandas`` objects
::::::::::::::::::::::::::::::::::::::::::::::::

.. currentmodule:: pandasdmx.writer.pandas

.. versionchanged:: 1.0

   :meth:`sdmx.to_pandas` handles all types of objects, replacing the earlier, separate ``data2pandas`` and ``structure2pd`` writers.

:func:`.to_pandas` implements a dispatch pattern according to the type of *obj*.
Some of the internal methods take specific arguments and return varying values.
These arguments can be passed to :func:`.to_pandas` when `obj` is of the appropriate type:

.. autosummary::
   pandasdmx.writer.pandas.write_dataset
   pandasdmx.writer.pandas.write_datamessage
   pandasdmx.writer.pandas.write_itemscheme
   pandasdmx.writer.pandas.write_structuremessage
   pandasdmx.writer.pandas.DEFAULT_RTYPE

Other objects are converted as follows:

:class:`.Component`
   The :attr:`~.Concept.id` attribute of the :attr:`~.Component.concept_identity` is returned.

:class:`.DataMessage`
   The :class:`.DataSet` or data sets within the Message are converted to pandas objects.
   Returns:

   - :class:`pandas.Series` or :class:`pandas.DataFrame`, if `obj` has only one data set.
   - list of (Series or DataFrame), if `obj` has more than one data set.

:class:`.dict`
   The values of the mapping are converted individually.
   If the resulting values are :class:`str` or Series *with indexes that share the same name*, then they are converted to a Series, possibly with a :class:`pandas.MultiIndex`.
   Otherwise, a :class:`.DictLike` is returned.

:class:`.DimensionDescriptor`
   The :attr:`~.DimensionDescriptor.components` of the DimensionDescriptor are written.

:class:`list`
   For the following *obj*, returns Series instead of a :class:`list`:

   - a list of :class:`.Observation`: the Observations are written using :meth:`write_dataset`.
   - a list with only 1 :class:`.DataSet` (e.g. the :attr:`~.DataMessage.data` attribute of :class:`.DataMessage`): the Series for the single element is returned.
   - a list of :class:`.SeriesKey`: the key values (but no data) are returned.

:class:`.NameableArtefact`
   The :attr:`~.NameableArtefact.name` attribute of `obj` is returned.

.. automodule:: pandasdmx.writer.pandas
   :members: DEFAULT_RTYPE, write_dataset, write_datamessage, write_itemscheme, write_structuremessage

.. todo::
   Support selection of language for conversion of
   :class:`InternationalString <sdmx.model.InternationalString>`.


``writer.xml``: Write to pandasdmx.ML
:::::::::::::::::::::::::::::::::::::

.. versionadded:: 1.1

See :func:`.to_xml`.


``remote``: Access pandasdmx.REST web services
----------------------------------------------
.. autoclass:: pandasdmx.remote.Session
.. autoclass:: pandasdmx.remote.ResponseIO


``source``: Features of pandasdmx.data sources
----------------------------------------------

This module defines :class:`Source <sdmx.source.Source>` and some utility functions.
For built-in subclasses of Source used to provide :mod:`sdmx`'s built-in support
for certain data sources, see :doc:`sources`.

.. autoclass:: pandasdmx.source.Source
   :members:

.. automodule:: pandasdmx.source
   :members: add_source, list_sources, load_package_sources


``util``: Utilities
-------------------
.. automodule:: pandasdmx.util
   :members:
   :undoc-members:
   :show-inheritance:
