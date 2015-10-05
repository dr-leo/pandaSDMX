=============
pandaSDMX
=============




pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ 
package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <http://www.sdmx.org>`_ format. 
It should work with all
SDMX data providers supporting SDMX 2.1. Currently,
this is tested for the European statistics office (Eurostat),
and the European Central Bank (ECB) each providing hundreds of
thousands of time series. 

While pandaSDMX is extensible to 
cater any output format, it currently supports only `pandas <http://pandas.pydata.org>`_, the gold-standard 
of data analysis in Python. But from pandas you can export your data to Excel and friends. 

Main features
---------------------

* intuitive API inspired by `requests <https://pypi.python.org/pypi/requests/>`_  
* support for many SDMX features including

  - generic datasets
  - data structure definitions, code lists and concept schemes
  - dataflow definitions and content-constraints
  - categorisations and category schemes

* pythonic representation of the SDMX information model  
* find dataflows by name or description in multiple languages if available
* When requesting datasets, validate column selections against code lists 
  and content-constraints if available 
* read and write SDMX messages to and from local files 
* configurable HTTP connections
* support for `requests-cache <https://readthedocs.org/projects/requests-cache/>`_ allowing to cache SDMX messages in 
  memory, MongoDB, Redis or SQLite  
* writer transforming SDMX generic datasets into multi-indexed pandas DataFrames or Series of observations and attributes 
* extensible through custom readers and writers for alternative input and output formats of data and metadata

For further details including extensive code examples
see the 
`documentation <http://pandasdmx.readthedocs.org>`_ . 


pandaSDMX Links
-------------------------------

* `Documentation <http://pandasdmx.readthedocs.org>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
 
  
  
Recent changes 
========================

v0.3.1 (2015-10-04)
-----------------------

This release fixes a few bugs which caused crashes in some situations. 

v0.3.0 (2015-09-22)
-----------------------


* support for `requests-cache <https://readthedocs.org/projects/requests-cache/>`_ allowing to cache SDMX messages in 
  memory, MongoDB, Redis or SQLite 
* pythonic selection of series when requesting a dataset:
  Request.get allows the ``key`` keyword argument in a data request to be a dict mapping dimension names 
  to values. In this case, the dataflow definition and datastructure 
  definition, and content-constraint
  are downloaded on the fly, cached in memory and used to validate the keys. 
  The dotted key string needed to construct the URL will be generated automatically. 
* The Response.write method takes a ``parse_time`` keyword arg. Set it to False to avoid
  parsing of dates, times and time periods as exotic formats may cause crashes.
* The Request.get method takes a ``memcache`` keyward argument. If set to a string,
  the received Response instance will be stored in the dict ``Request.cache`` for later use. This is useful
  when, e.g., a DSD is needed multiple times to validate keys.
* fixed base URL for Eurostat  
* major refactorings to enhance code maintainability

v0.2.2 (2015-05-19)
-------------------------------

* Make HTTP connections configurable by exposing the 
  `requests.get API <http://www.python-requests.org/en/latest/>`_ 
  through the ``pandasdmx.api.Request`` constructor.
  Hence, proxy servers, authentication information and other HTTP-related parameters consumed by ``requests.get`` can be
  set for an ``Request`` instance and used in subsequent requests. The configuration is
  exposed as a dict through the ``Request.client.config`` attribute.
* Responses now have an ``http_headers`` attribute containing the headers returned by the SDMX server


v0.2.1 (2015-04-22)
----------------------------------

* API: add support for zip archives received from an SDMX server. 
  This is common for large datasets from Eurostat
* incidentally get a remote resource if the footer of a received message
  specifies an URL. This pattern is common for large datasets from Eurostat.
* allow passing a file-like object to api.Request.get() 
* enhance documentation
* make pandas writer parse more time period formats and increase its performance  
  
v0.2.0 (2015-04-13)
------------------------------------


This version is a quantum leap. The whole project has been redesigned and rewritten from
scratch to provide robust support for many SDMX features. The new architecture is centered around
a pythonic representation of the SDMX information model. It is extensible through readers and writers
for alternative input and output formats. 
Export to pandas has been dramatically improved. Sphinx documentation
has been added.

v0.1 (2014-09)
----------------

Initial release

 


