pandaSDMX: Statistical Data and Metadata eXchange in Python
=============================================================


pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ 
client to retrieve and acquire statistical data
and metadata disseminated in
`SDMX <http://www.sdmx.org>`_ 2.1, an ISO-standard
widely used by institutions
such as statistics offices, central banks, and international organisations.
pandaSDMX exposes datasets and related structural metadata 
including dataflows, code-lists, 
and datastructure definitions as `pandas <http://pandas.pydata.org>`_ Series 
or multi-indexed DataFrames. Many other 
output formats and storage backends are available thanks to `Odo <http://odo.readthedocs.io/>`_.  

Supported data providers
----------------------------
pandaSDMX ships with built-in support for the following agencies (others may be  
configured by the user): 

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
---------------------

* support for many SDMX features including

  - both generic and structure-specific data sets in SDMXML format 
  - data sets in SDMXJSON format  
  - data structure definitions, code lists and concept schemes
  - dataflow definitions and content-constraints
  - categorisations and category schemes

* pythonic representation of the SDMX information model  
* When requesting datasets, validate column selections against code lists 
  and content-constraints if available
* export data and structural metadata such as code lists as multi-indexed pandas DataFrames or Series, and
  many other formats as well as database backends via `Odo`_ 
* read and write SDMX messages to and from files 
* configurable HTTP connections
* support for `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ allowing to cache SDMX messages in 
  memory, MongoDB, Redis or SQLite  
* extensible through custom readers and writers for alternative input and output formats 
* growing test suite

Example
---------

Suppose we want to analyze annual unemployment data for some European countries. All we need to know
in advance is the data provider, eurostat. pandaSDMX makes it super easy to
search the directory of dataflows, and the complete structural metadata about the datasets
available through the selected dataflow. We will skip this step here.
The impatient reader may directly jump to :ref:`basic-usage`. 
The dataflow with the ID 'une_rt_a' contains the data we want. The dataflow definition references a 
datastructure definition with the ID 'DSD_une_rt_a'. 
It contains or references all the metadata describing data sets available through this dataflow: the dimensions, 
concept schemes, and corresponding code lists. 
 
.. ipython:: python

    from pandasdmx import Request
    estat = Request('ESTAT')
    # Download the metadata and expose it as a dict mapping resource names to pandas DataFrames
    metadata = estat.datastructure('DSD_une_rt_a').write()
    # Show some code lists.
    metadata.codelist.iloc[8:18]
    
Next we download a dataset. We use codes from the code list 'GEO'
to obtain data on Greece, Ireland and Spain only.

.. ipython:: python

    resp = estat.data('une_rt_a', key={'GEO': 'EL+ES+IE'}, params={'startPeriod': '2007'})
    # We use a generator expression to select some columns 
    # and write them to a pandas DataFrame
    data = resp.write(s for s in resp.data.series if s.key.AGE == 'TOTAL')
    # Explore the data set. First, show dimension names
    data.columns.names
    # and corresponding dimension values
    data.columns.levels
    # Show aggregate unemployment rates across ages and sexes as
    # percentage of active population 
    data.loc[:, ('PC_ACT', 'TOTAL', 'T')]

Quick install
-----------------

* ``pip install pandasdmx``


pandaSDMX Links
-------------------------------

* `Download the latest stable version from the Python package index <https://pypi.python.org/pypi/pandaSDMX>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
* `Official SDMX website <http://www.sdmx.org>`_ 
 
Table of contents
---------------------


.. toctree::
    :maxdepth: 2
    :numbered:

    whatsnew
    faq
    intro
    sdmx_tour
    usage
    agencies
    advanced
    API documentation <api/modules>
    contributing
    license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

