Statistical Data and Metadata eXchange (SDMX) in Python
*******************************************************

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
- apply the :ref:`SDMX Information Model <im>` to your own data;

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

To learn about SDMX in more detail, use the resources linked from the :doc:`overview <overview>`, or read the API documentation for the :mod:`pandasdmx.model` and :mod:`pandasdmx.message` modules that fully implement the IM.

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
   howto
   whatsnew
   roadmap


Contributing to pandaSDMX and getting help
==========================================

- Report bugs, suggest features or view the source code on
  `GitHub <https://github.com/dr-leo/pandaSDMX>`_.
- The :doc:`overview` contains references to other learning materials and miscellaneous notes.
- The `sdmx-python <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_ Google Group and mailing list may have answers for some questions.

..

- :doc:`glossary`
- :doc:`license`
- :ref:`genindex`

.. toctree::
   :hidden:

   overview
   glossary
   license
