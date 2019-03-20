pandaSDMX: Statistical Data and Metadata eXchange in Python
===========================================================

pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ library
that implements `SDMX <http://www.sdmx.org>`_ 2.1
(`ISO 17369:2013 <https://www.iso.org/standard/52500.html>`_) a format for
exchange of **statistical data and metadata** used by national statistical
agencies, central banks, and international organisations.

pandaSDMX can be used to:

- explore the data available from many :doc:`data providers <sources>`;
- retrieve data from SDMX web services, or from files;
- convert data into `Pandas <http://pandas.pydata.org>`_ objects, for easy
  use in analysis, plotting, and other tools in the Python data science
  ecosystem; and
- apply the :doc:`SDMX Information Model <im>` to your own data.

Other features
--------------

- Built-in support for remote data sources including:

  - `Australian Bureau of Statistics <http://www.abs.gov.au>`_
  - `European Central Bank <http://www.ecb.europa.eu>`_
  - `Eurostat <http://ec.europa.eu/eurostat/>`_
  - L'`Institut national de la statistique et des études économiques <https://insee.fr>`_ (INSEE), or National Institute of Statistics and Economic Studies (France).
  - `International Monetary Fund (IMF) - SDMX Central only <https://sdmxcentral.imf.org/>`_
  - `Organisation for Economic Cooperation and Development (OECD) <http://stats.oecd.org/SDMX-JSON/>`_
  - `UN Statistics Division (UNSD) <https://unstats.un.org/home/>`_
  - `UNESCO <https://apiportal.uis.unesco.org/getting-started>`_
  - `World Bank <https://wits.worldbank.org>`_

- Full parsers for the SDMX-ML (XML) and SDMX-JSON message formats.
- Pythonic representation of the SDMX Information Model.
- Query validation against content constraints and code lists.
- Local file input.
- Configurable HTTP connections and response caching.
- Full test coverage.

Documentation
-------------

SDMX is extremely powerful, designed to be flexible enough to accommodate
almost *any* data. This also means it is complex, with many abstract concepts.
These are called the SDMX “Information Model” (IM)—a way of talking about data
and metadata concepts that can be applied broadly.

The pandaSDMX documentation mainly omits details of the IM to focus on the
functionality provided by the package itself. Detailed knowledge of the IM is
not needed to use pandaSDMX; see a
:doc:`usage example in only 10 lines of code <example>`!

To learn about the IM and unlock the full power of SDMX, users can skim the
:doc:`short introduction to SDMX <intro>`, consult the linked reference
materials, and read the API documentation for the :mod:`pandasdmx.model` and
:mod:`pandasdmx.message` modules that implement SDMX.

**Getting started**

* :doc:`example`
* :doc:`install`
* :doc:`walkthrough`
* :doc:`intro`

.. toctree::
   :hidden:

   10-line example <example>
   install
   walkthrough
   Intro to SDMX <intro>

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
* :doc:`faq`
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
   faq
   roadmap
   license
