pandaSDMX: Statistical Data and Metadata eXchange in Python
===========================================================

pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ library to
retrieve and acquire statistical data and metadata disseminated in `SDMX
<http://www.sdmx.org>`_ 2.1, an ISO-standard widely used by institutions such as
statistics offices, central banks, and international organisations.  pandaSDMX
exposes datasets and related structural metadata including dataflows,
code-lists, and datastructure definitions as `pandas
<http://pandas.pydata.org>`_ Series or multi-indexed DataFrames. Many other
output formats and storage backends are available thanks to `Odo
<http://odo.readthedocs.io/>`_.


Supported data sources
------------------------
pandaSDMX ships with built-in support for the following :doc:`sources`, and
allows others to be configured by the user:

* `Australian Bureau of Statistics (ABS) <http://www.abs.gov.au/>`_
* `European Central Bank (ECB) <http://www.ecb.europa.eu/stats/ecb_statistics/co-operation_and_standards/sdmx/html/index.en.html>`_
* `Eurostat <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`_
* `French National Institute for Statistics (INSEE)
  <http://www.bdm.insee.fr/bdm2/statique?page=sdmx>`_
* `International Monetary Fund (IMF) - SDMX Central only
  <https://sdmxcentral.imf.org/>`_
* `Organisation for Economic Cooperation and Development (OECD)
  <http://stats.oecd.org/SDMX-JSON/>`_
* `United Nations Statistics Division (UNSD) <https://unstats.un.org/home/>`_
* `UNESCO (free registration required) <https://apiportal.uis.unesco.org/getting-started>`_
* `World Bank - World Integrated Trade Solution (WITS) <wits.worldbank.org>`_

Main features
-------------

* support for many SDMX features including

  - generic data sets in SDMXML format
  - data sets in SDMXJSON format
  - data structure definitions, code lists and concept schemes
  - dataflow definitions and content-constraints
  - categorisations and category schemes

* pythonic representation of the SDMX information model
* When requesting datasets, validate column selections against code lists
  and content-constraints if available
* export data and structural metadata such as code lists as multi-indexed
  pandas DataFrames or Series, and many other formats as well as database
  backends via `Odo`_
* read and write SDMX messages to and from files
* configurable HTTP connections
* support for `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ allowing to cache SDMX messages in memory, MongoDB, Redis or SQLite
* extensible through custom readers and writers for alternative input and
  output formats
* growing test suite

Documentation
-------------

**Getting started**

* :doc:`example`
* :doc:`faq`
* :doc:`install`

.. toctree::
   :hidden:

   example
   faq
   install

The following chapters explain the key characteristics of SDMX, demonstrate the
basic usage of pandaSDMX and provide additional information on some advanced
topics. While users that are new to SDMX are likely to benefit a lot from
reading the next chapter on SDMX, normal use of pandaSDMX should not strictly
require this.  The :ref:`Basic usage <basic-usage>` chapter should enable you to
retrieve datasets and write them to pandas DataFrames. But if you want to
exploit the full richness of the information model, or simply feel more
comfortable if you know what happens behind the scenes, the :ref:`SDMX
introduction <sdmx-tour>` is for you. It also contains links to reference
materials on SDMX.


**User guide**

* :doc:`sources`
* :doc:`im`
* :doc:`api`

.. toctree::
    :hidden:

    sources
    im
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

Original documentation
----------------------

.. toctree::
   :maxdepth: 1

   sdmx_tour
   usage
   advanced
