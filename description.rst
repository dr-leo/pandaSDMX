=============
pandaSDMX
=============



pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ 
package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <http://www.sdmx.org>`_ format. 
It supports out of the box 
the SDMX services of the European statistics office (Eurostat), 
the European Central Bank (ECB), and the French National Institute for statistics (INSEE). 
pandaSDMX can export data and metadata as `pandas <http://pandas.pydata.org>`_ DataFrames, 
the gold-standard 
of data analysis in Python. 
From pandas you can export data and metadata to Excel, R and friends. As from version 0.4, 
pandaSDMX can export data to many other file formats and
database backends via `Odo <odo.readthedocs.io/>`_. 

Main features
==================

* intuitive API inspired by `requests <https://pypi.python.org/pypi/requests/>`_  
* support for many SDMX features including

  - generic datasets
  - data structure definitions, code lists and concept schemes
  - dataflow definitions and content-constraints
  - categorisations and category schemes

* pythonic representation of the SDMX information model  
* When requesting datasets, validate column selections against code lists 
  and content-constraints if available
* export data and metadata as multi-indexed pandas DataFrames or Series, and
  many other formats and database backends via `Odo <odo.readthedocs.io/>`_ 
* read and write SDMX messages to and from local files 
* configurable HTTP connections
* support for `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ allowing to cache SDMX messages in 
  memory, MongoDB, Redis or SQLite  
* extensible through custom readers and writers for alternative input and output formats of data and metadata
* growing test suite

For further details including extensive code examples
see the 
`documentation <http://pandasdmx.readthedocs.io>`_ . 


pandaSDMX Links
-------------------------------

* `Documentation <http://pandasdmx.readthedocs.io>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
 
  
  
Recent changes 
========================


v0.5dev (2016-07-11)
-----------------------

New features
~~~~~~~~~~~~~~~~

* new reader module for SDMX JSON data messages
* add OECD as data provider (data messages only)
* pandasdmx.model.Category is now an iterator over categorised objects. This greatly simplifies category usage.
  Besides, categories with the same ID while belonging to
  multiple category schemes are no longer conflated.  


API changes
~~~~~~~~~~~~~~~

* Request constructor: make agency ID case-insensitive
* As Category is now an iterator over categorised objects, Categorisations
  is no longer considered part of the public API. 
 
Bug fixes
~~~~~~~~~~~~~~~~~~~~~~
 
* sdmxml reader: fix AttributeError in write_source method, thanks to Topas
* correctly distinguish between categories with same ID while belonging to different category schemes  



v0.4 (2016-04-11)
-----------------------

New features
~~~~~~~~~~~~~~

* add new provider INSEE, the French statistics office (thanks to Stéphan Rault)
* register '.sdmx' files with `Odo <odo.readthedocs.io/>`_ if available
* logging of http requests and file operations.
* new structure2pd writer to export codelists, dataflow-definitions and other
  structural metadata from structure messages 
  as multi-indexed pandas DataFrames. Desired attributes can be specified and are
  represented by columns.
  
API changes
~~~~~~~~~~~~~

* `pandasdmx.api.Request` constructor accepts a ``log_level`` keyword argument which can be set
  to a log-level for the pandasdmx logger and its children (currently only pandasdmx.api)
* `pandasdmx.api.Request` now has a ``timeout`` property to set
  the timeout for http requests
* extend api.Request._agencies configuration to specify agency- and resource-specific 
  settings such as headers. Future versions may exploit this to provide 
  reader selection information.
* api.Request.get: specify http_headers per request. Defaults are set according to agency configuration   
* Response instances expose Message attributes to make application code more succinct
* rename `pandasdmx.api.Message` attributes to singular form
  Old names are deprecated and will be removed in the future.
* `pandasdmx.api.Request` exposes resource names such as data, datastructure, dataflow etc. 
  as descriptors calling 'get' without specifying the resource type as string. 
  In interactive environments, this
  saves typing and enables code completion. 
* data2pd writer: return attributes as namedtuples rather than dict
* use patched version of namedtuple that accepts non-identifier strings 
  as field names and makes all fields accessible through dict syntax.
* remove GenericDataSet and GenericDataMessage. Use DataSet and DataMessage instead
* sdmxml reader: return strings or unicode strings instead of LXML smart strings
* sdmxml reader: remove most of the specialized read methods. 
  Adapt model to use generalized methods. This makes code more maintainable.  
* `pandasdmx.model.Representation` for DSD attributes and dimensions now supports text
  not just codelists.

Other changes and enhancements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* documentation has been overhauled. Code examples are now much simpler thanks to
  the new structure2pd writer
* testing: switch from nose to py.test
* improve packaging. Include tests in sdist only
* numerous bug fixes

v0.3.1 (2015-10-04)
-----------------------

This release fixes a few bugs which caused crashes in some situations. 

v0.3.0 (2015-09-22)
-----------------------


* support for `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ allowing to cache SDMX messages in 
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

 


