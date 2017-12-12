=============
pandaSDMX
=============

pandaSDMX is an Apache 2.0-licensed  
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

  - generic and structure-specific data sets in SDMXML format
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

For further details including release notes and extensive code examples
see the 
`documentation <http://pandasdmx.readthedocs.io>`_ . 


pandaSDMX Links
-------------------------------

* `Documentation <http://pandasdmx.readthedocs.io>`_
* `Google group <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
 
  
