:tocdepth: 1

What's new?
==============

v0.8.2 (2017-12-21)
----------------------------

* fix reading of structure-specific data sets when DSD_ID is present in the data set

v0.8.1 (2017-12-20)
----------------------------

* fix broken  package preventing pip installs of the wheel 


v0.8 (2017-12-12)
----------------------------

* add support for an alternative data set format 
  defined for SDMXML messages. These so-called  structure-specific data sets lend themselves
  for large data queries. File sizes are typically
  about 60 % smaller than with equivalent generic data sets. To make use of 
  structure-specific data sets, instantiate Request 
  objects with agency IDs such as   
  'ECB_S', 'INSEE_S' or 'ESTAT_S' instead of 'ECB' etc.
  These alternative agency profiles prompt pandaSDMX to execute data queries for structure-specific data sets.
  For all other queries they behave exactly as their siblings. 
  See a code example in chapter 5 of the docs.
* raise ValueError when user attempts to request a resource other than data
  from an agency delivering data in SCMX-JSON format only (OECD and ABS).
* Update INSEE profile
* handle empty series properly
* data2pd writer: the code for Series index generation was rewritten from scratch to make
  better use of pandas' time series functionality. However, some data sets, in particular from INSEE, which
  come with bimonthly or semestrial frequencies cannot be rendered as PeriodIndex. Pass
  ``parse_time=False`` to the .write method to prevent errors.
  

v0.7.0 (2017-06-10)
----------------------------

* add new data providers:
 
  - Australian Bureau of Statistics
  - International Monetary Fund - SDMXCentral only
  - United Nations Division of Statistics
  - UNESCO (free registration required)
  - World Bank - World Integrated Trade Solution (WITS)  
  
* new feature: load metadata on data providers from json file; allow the user to
  add new agencies on the fly by specifying an appropriate
  JSON file using the :meth:`pandasdmx.api.Request.load_agency_profile`.
* new :meth:`pandasdmx.api.Request.preview_data` providing a 
  powerful fine-grain key validation algorithm by downloading all series-keys of a dataset and 
  exposing them as a pandas DataFrame which is then mapped to the cartesian product 
  of the given dimension values. Works only with
  data providers such as ECB and UNSD which support "series-keys-only" requests. This
  feature could be wrapped by a browser-based UI for building queries.   
* sdjxjson reader: add support for flat and
  cross-sectional datasets, preserve dimension order where possible
* structure2pd writer: in codelists, output Concept rather than Code attributes in the first
  line of each code-list. This may provide more
  information.  

v0.6.1 (2017-02-03)
----------------------------

* fix 2to3 issue which caused crashes on Python 2.7


v0.6 (2017-01-07)
-----------------------

This release contains some important stability improvements.

Bug fixes
:::::::::::::::
  
* JSON data from OECD
  is now properly downloaded 
* The data writer tries to gleen a frequency value for a time series from its attributes.
  This is helpful when exporting data sets, e.g., from INSEE 
  (`Issue 41 <https://github.com/dr-leo/pandaSDMX/issues/41>`_).
 
Known issues
:::::::::::::::
  
A data set which lacks a FREQ dimension or attribute can be
exported as pandas DataFrame only when `parse_time=False?`, i.e. no DateTime index
is generated. The resulting DataFrame has a string index. Use pandas magic to
create a DateTimeIndex from there.   

v0.5 (2016-10-30)
-----------------------

New features
:::::::::::::::::

* new reader module for SDMX JSON data messages
* add OECD as data provider (data messages only)
* :class:`pandasdmx.model.Category` is now an iterator over categorised objects. This greatly simplifies category usage.
  Besides, categories with the same ID while belonging to
  multiple category schemes are no longer conflated.  


API changes
:::::::::::::::

* Request constructor: make agency ID case-insensitive
* As :class:`Category` is now an iterator over categorised objects, :class:`Categorisations`
  is no longer considered part of the public API. 
 
Bug fixes
:::::::::::::::
 
* sdmxml reader: fix AttributeError in write_source method, thanks to Topas
* correctly distinguish between categories with same ID while belonging to different category schemes  


v0.4 (2016-04-11)
-----------------------

New features
::::::::::::::

* add new provider INSEE, the French statistics office (thanks to Stéphan Rault)
* register '.sdmx' files with `Odo <odo.readthedocs.io/>`_ if available
* logging of http requests and file operations.
* new structure2pd writer to export codelists, dataflow-definitions and other
  structural metadata from structure messages 
  as multi-indexed pandas DataFrames. Desired attributes can be specified and are
  represented by columns.
  
API changes
:::::::::::::

* :class:`pandasdmx.api.Request` constructor accepts a ``log_level`` keyword argument which can be set
  to a log-level for the pandasdmx logger and its children (currently only pandasdmx.api)
* :class:`pandasdmx.api.Request` now has a ``timeout`` property to set
  the timeout for http requests
* extend api.Request._agencies configuration to specify agency- and resource-specific 
  settings such as headers. Future versions may exploit this to provide 
  reader selection information.
* api.Request.get: specify http_headers per request. Defaults are set according to agency configuration   
* Response instances expose Message attributes to make application code more succinct
* rename :class:`pandasdmx.api.Message` attributes to singular form
  Old names are deprecated and will be removed in the future.
* :class:`pandasdmx.api.Request` exposes resource names such as data, datastructure, dataflow etc. 
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
* :class:`pandasdmx.model.Representation` for DSD attributes and dimensions now supports text
  not just codelists.

Other changes and enhancements
::::::::::::::::::::::::::::::::::

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

v0.2.2
--------------

* Make HTTP connections configurable by exposing the 
  `requests.get API <http://www.python-requests.org/en/latest/>`_ 
  through the :class:`pandasdmx.api.Request` constructor.
  Hence, proxy servers, authorisation information and other HTTP-related parameters consumed by ``requests.get`` can be
  specified for each ``Request`` instance and used in subsequent requests. The configuration is exposed as a dict through
  a new ``Request.client.config`` attribute.
* Responses have a new ``http_headers`` attribute containing the HTTP headers returned by the SDMX server

v0.2.1
--------------

* Request.get: allow `fromfile` to be a file-like object
* extract SDMX messages from zip archives if given. Important for large datasets from Eurostat
* automatically get a resource at an URL given in
  the footer of the received message. This allows to automatically get large datasets from Eurostat that have been
  made available at the given URL. The number of attempts and the time to wait before each
  request are configurable via the ``get_footer_url`` argument. 
 

v0.2 (2015-04-13)
-----------------------

This version is a quantum leap. The whole project has been redesigned and rewritten from
scratch to provide robust support for many SDMX features. The new architecture is centered around
a pythonic representation of the SDMX information model. It is extensible through readers and writers
for alternative input and output formats. 
Export to pandas has been dramatically improved. Sphinx documentation
has been added.

v0.1 (2014-09)
----------------

Initial release

 

