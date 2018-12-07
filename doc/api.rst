API reference
=================

Top-level methods and classes
-----------------------------

.. automodule:: pandasdmx
   :members:

``pandasdmx.message``: SDMX messages
------------------------------------

.. automodule:: pandasdmx.message
   :members:
   :undoc-members:
   :show-inheritance:

``pandasdmx.reader``: Parsers for SDMX file formats
---------------------------------------------------

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


``pandasdmx.writer``: Convert SDMX to pandas objects
----------------------------------------------------

.. autoclass:: pandasdmx.writer.Writer
    :members:
    :undoc-members:


``pandasdmx.remote``: Utilities for accessing SDMX REST web services
--------------------------------------------------------------------

.. autoclass:: pandasdmx.remote.Session
.. autoclass:: pandasdmx.remote.ResponseIO


``pandasdmx.source``: Features for specific SDMX data sources
-------------------------------------------------------------

Built-in subclasses of :class:`pandasdmx.source.Source` are described at
:doc:`sources`.

.. autoclass:: pandasdmx.source.Source

``pandasdmx.util``: Utilities
-----------------------------

.. automodule:: pandasdmx.util
    :members:
    :undoc-members:
    :show-inheritance:
