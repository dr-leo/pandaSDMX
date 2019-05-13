Statistical Data and Metadata eXchange (SDMX) in Python
=======================================================

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
- apply the :doc:`SDMX Information Model <im>` to your own data;

…and much more.

Documentation
-------------

SDMX was designed to be flexible enough to accommodate almost *any* data.
This also means it is complex, with many abstract concepts for describing data,
metadata, and their relationships.
These are called the “SDMX Information Model” (IM).

This documentation does not repeat the full description of the IM, but focuses on functionality provided by :mod:`pandaSDMX` itself.
Detailed knowledge of the IM is not needed to use :mod:`pandaSDMX`; see a
:doc:`usage example in only 10 lines of code <example>`.

To learn about the IM and unlock the full power of SDMX, users can skim a :doc:`short introduction <intro>`, consult the linked reference materials, and/or read the API documentation for the :mod:`pandasdmx.model` and :mod:`pandasdmx.message` modules that implement it.

**Getting started**

* :doc:`example`
* :doc:`install`
* :doc:`walkthrough`
* :doc:`intro`
* :doc:`howto`

.. toctree::
   :hidden:

   10-line example <example>
   install
   walkthrough
   Intro to SDMX <intro>
   howto

**User guide**

* :doc:`sources`
* :doc:`im`
* :doc:`api`

.. toctree::
    :hidden:

    sources
    Information model <im>
    api

**Help & development**

* :doc:`whatsnew`
* Report bugs, suggest features or view the source code on
  `Github <https://github.com/dr-leo/pandaSDMX>`_; or use the `mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_ for other questions.
* :doc:`roadmap`
* :doc:`license`
* :ref:`genindex`
* External links:

  * `Official SDMX website <http://www.sdmx.org>`_


.. toctree::
   :hidden:

   whatsnew
   roadmap
   license
