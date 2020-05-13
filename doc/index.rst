Statistical Data and Metadata eXchange (SDMX) for the  Python data  ecosystem
********************************************************************************

:mod:`pandaSDMX` is an Apache 2.0-licensed `Python <http://www.python.org>`_ library that implements `SDMX <http://www.sdmx.org>`_ 2.1
(`ISO 17369:2013 <https://www.iso.org/standard/52500.html>`_), a format for
exchange of **statistical data and metadata** used by national statistical
agencies, central banks, and international organisations.

:mod:`pandaSDMX` can be used to:

- explore the data available from :doc:`data providers <sources>` such as the World Bank, International Monetary Fund, Eurostat, OECD, and United Nations;
- parse data and metadata in SDMX-ML (XML) or SDMX-JSON formats—either:

  - from local files, or
  - retrieved from SDMX web services, with query validation and caching;

- convert data and metadata into `pandas <http://pandas.pydata.org>`_ objects,
  for use with the analysis, plotting, and other tools in the Python data
  science ecosystem;
- apply the :doc:`SDMX Information Model <implementation>` to your own data;

…and much more.

Get started
===========

SDMX was designed to be flexible enough to accommodate almost *any* data.
This also means it is complex, with many abstract concepts for describing data,
metadata, and their relationships.
These are called the “SDMX Information Model” (IM).

.. _not-the-standard:

This documentation does not repeat full descriptions of SDMX, the IM, or SDMX web services; it focuses on functionality provided by :mod:`pandaSDMX` itself.
Detailed knowledge of the IM is not needed to use :mod:`pandaSDMX`; see a
:doc:`usage example in only 10 lines of code <example>`, and then the longer, narrative :doc:`walkthrough <walkthrough>`.

To learn about SDMX in more detail, use the :doc:`list of resources and references <resources>`, or read the :doc:`API documentation <api>` and :doc:`implementation notes <implementation>` for the :mod:`pandasdmx.model` and :mod:`pandasdmx.message` modules that  implement the IM.

.. toctree::
   :maxdepth: 1

   example
   install
   walkthrough


:mod:`pandaSDMX` user guide
===========================

.. toctree::
   :maxdepth: 2

   sources
   api
   implementation
   howto
   whatsnew
   roadmap


Contributing to pandaSDMX and getting help
==========================================

- Report bugs, suggest features or view the source code on
  `GitHub <https://github.com/dr-leo/pandaSDMX>`_.
- The `sdmx-python <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_ Google Group and mailing list may have answers for some questions.


.. toctree::

   resources
   glossary
   license

- :ref:`genindex`
