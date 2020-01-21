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
See :ref:`im`.

.. automodule:: pandasdmx.model
   :members:
   :undoc-members:
   :show-inheritance:

``reader``: Parsers for SDMX file formats
-----------------------------------------

SDMX-ML
:::::::
.. currentmodule:: pandasdmx.reader.sdmxml

pandaSDMX supports the several types of SDMX-ML messages.

.. autoclass:: pandasdmx.reader.sdmxml.Reader
    :members:
    :undoc-members:

SDMX-JSON
:::::::::

.. currentmodule:: pandasdmx.reader.sdmxjson

.. autoclass:: pandasdmx.reader.sdmxjson.Reader
    :members:
    :undoc-members:


``writer``: Convert SDMX to pandas objects
------------------------------------------
.. versionchanged:: 1.0

   :meth:`pandasdmx.to_pandas` (via :meth:`write <pandasdmx.writer.write>`)
   handles all types of objects, replacing the earlier, separate
   ``data2pandas`` and ``structure2pd`` writers.

.. automodule:: pandasdmx.writer
   :members:
   :exclude-members: write

   .. automethod:: pandasdmx.writer.write

      .. autosummary::
         write_component
         write_dataset
         write_dict
         write_dimensiondescriptor
         write_itemscheme
         write_list
         write_nameableartefact
         write_response
         write_serieskeys
         write_structuremessage

.. todo::
   Support selection of language for conversion of
   :class:`InternationalString <pandasdmx.model.InternationalString>`.



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
