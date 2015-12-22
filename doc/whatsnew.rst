:tocdepth: 1

What's new?
==============

v0.4.0 (2015-12)
-----------------------

* module-level logging. Used for making requests or loading and saving files.
  ``pandasdmx.api.Request`` constructor accepts a ``log_level`` keyword arg which can be set
  to a log-level for the pandasdmx logger and its children (currently only pandasdmx.api)
*  ``pandasdmx.api.Request`` has a ``set_timeout`` convenience method to set
  the timeout for http requests   
* Responses expose Message attributes to save typing
* Requests expose resource names such as data, datastructure, dataflow etc. 
  as descriptors calling 'get' without specifying the resource type as string. 
  In interactive environments, this
  saves typing and enables code completion. 
* add structure2pd writer to export codelists, dataflow-definitions and other
  nameable SDMX artefacts from structure messages 
  as multi-indexed DataFrames. Desired attributes can be specified and are
  represented by columns. 
* data2pd writer: return attributes as namedtuples rather than dict
* testing: switch from nose to py.test
* sdmxml reader: return strings or unicode strings instead of LXML smart strings
* lots of bug fixes and code clean-ups

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

 

