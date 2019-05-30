API reference
=============

.. contents::
   :local:
   :backlinks: none

Top-level methods and classes
-----------------------------
.. automodule:: pandasdmx
   :members:

``message``: SDMX messages
--------------------------
.. automodule:: pandasdmx.message
   :members:
   :undoc-members:
   :show-inheritance:

``model``: SDMX Information Model
---------------------------------
See :doc:`im`.

.. automodule:: pandasdmx.model
   :members:
   :undoc-members:
   :show-inheritance:

``reader``: Parsers for SDMX file formats
-----------------------------------------
SDMX-ML
:::::::

.. autoclass:: pandasdmx.reader.sdmxjson.Reader
    :members:
    :undoc-members:

SDMX-JSON
:::::::::

.. autoclass:: pandasdmx.reader.sdmxml.Reader
    :members:
    :undoc-members:


``writer``: Convert SDMX to pandas objects
------------------------------------------
Convert :mod:`model <pandasdmx.model>` and :mod:`message <pandasdmx.message>`
objects to :mod:`pandas` objects.

.. versionchanged:: 0.6

   Two writers are available:

   - ``data2pandas`` exports a dataset or portions thereof to a pandas DataFrame
     or Series.
   - ``structure2pd`` exports structural metadata such as lists of data-flow
     definitions, code-lists, concept-schemes etc. which are contained in a
     structural SDMX message as a dict mapping resource names (e.g. 'dataflow',
     'codelist') to pandas DataFrames.

.. versionchanged:: 1.0

   The :meth:`write <pandasdmx.writer.write>` method
   (:meth:`pandasdmx.to_pandas`) handles all types of objects.

.. automodule:: pandasdmx.writer
   :members:


``remote``: Access SDMX REST web services
-----------------------------------------
.. autoclass:: pandasdmx.remote.Session
.. autoclass:: pandasdmx.remote.ResponseIO


``source``: Features of SDMX data sources
-----------------------------------------

This module defines :class:`Source <pandasdmx.source.Source>` and some utility functions.
For built-in subclasses of Source used to provide pandaSDMX's built-in support
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
