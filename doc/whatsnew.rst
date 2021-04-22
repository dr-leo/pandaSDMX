:tocdepth: 1

What's new?
===========


v1.5.0 (2021-04-11)
-------------------------------

* Added Bank for International Settlements (BIS) as new data source


v1.4.2 (2021-03-26)
-------------------------------

* dependencies: set range for pydantic to >=1.7.1,<1.8 for now


v1.4.1 (2021-02-25)
-------------------------------

* Fix reader discovery for footer messages from ESTAT 
  when  querying large datasets which ESTAT delivers through a link to a zip file 

v1.4.0 (2021-02-04)
-------------------------------

* update end point link for ECB data source
* update data source config for ILO enabling access to its new API. 
  Remove obsolete adapter. Please report any issues.
* Add three new data sources (all of which support the sdmxjson format, 
  hence only data requests are allowed:
  - National Bank of Belgium (NBB)
  - Statistics Lithuania (LSB)
  - Statistics Estonia

v1.3.0 (2021-01-03)
-------------------------------

* Add new data source `Pacific Data Hub <https://stats.pacificdata.org/?locale=en>`_
* add support for Python 3.9
* properly validate URLs in source.Source
* sources.json: add URLs to documentation on data sources 
* api.Request: add method `view_doc` to view doc website
  in a new browser tab
* bug fix: propagate all relevant  kwargs to remote.Session
* Bug fix in source.ESTAT: honor get_footer_url arg for interval and frequency to download zip file
* CI: move from travis-ci to GitHub Actions

v1.2.0 (2020-11-XX)
-------------------------------

* Add new data source: World Bank - World Development Indicators
* Pass files for reading and writing in a with-context. See the documentation for  :func:`pandasdmx.reader.read_sdmx` and :meth:`pandasdmx.api.Request.get` for details
* Allow `FSSPEC <https://filesystem-spec.readthedocs.io/en/latest/>`_ files.
  Hence, all major cloud storage providers can be leveraged directly, 
  alonside many other features of FSSPEC.
* merge improvements from khaeru/sdmx1 fork: write DataMessages to SDMXML

v1.1.0 (2020-08-02)
-------------------------------

Overview
-------------------

This is a major feature release. The SDMXML reader has been refactored. It now uses an event-driven XML parser. In future releases, this may  allow parsing of large XML files which do not fit into memory. 

Changes
::::::::::

- add support for new data source 
  `Countdown2030 <https://profiles.countdown2030.org/>`_ 
- add support for new data source 
  `UNICEF <https://data.unicef.org/sdmx-api-documentation/>`_
- Remove data source UNESCO  as their SDMX web API has been discontinued.
  Bulk downloads should still be available though.
- Ported code-base   from v1.2.0 of recent 
  `fork <http://sdmx1.readthedocs.io/>`_. New features: 
  * event-driven SDMXML reader
  * new sdmxml writer to serialize a programmatically generated model representation as SDMXML file (in case anyone  needs this)  
- Fix crash when passing `str` typed filepath to :func:`pandasdmx.reader.read_sdmx`
- Add support for :class:`pandasdmx.message.DataMessage` attributes 
  *reporting_begin*, *reporting_en* and *extracted*.
- remove test suite from source distribution and wheels as the test suite has become rather unwieldy
  (E.g., on first run, 300MB of data are downloaded.)
- Do not raise `XMLParseError` and terminate when an unsupported tag is found in SDMXML 
  message. A gentle warning is logged instead.

Migrating from v1.0.x
:::::::::::::::::::::::::

No code-breaking changes are known so far. However, due to the new SDMX-ML reader design, performance of reading XML messages is further reduced by a factor of about six. Compared to v0.9, reading a large SDMX-ML message may take about 150 to 200 times longer. However, the new reader benefits from cleaner code and flexibility as regards memory footprint. 

v1.0.1 (2020-05-28)
-------------------------------

This release fixes a number of bugs and update resources.

- IMF no longer accepts data queries. Update source and docs to reflect this.
- Fix crash when making data requests to JSON-based data sources

v1.0.0 (2020-05-15)
-------------------------------

Overview
:::::::::::::

- :mod:`pandasdmx.model` has been reimplemented from the ground up. 
  Fundamental concepts have not changed though.

  - Python typing_ and pydantic_ are used to enforce compliance with the
    SDMX Information Model (IM). Users familiar with the IM can use
    :mod:`pandaSDMX` without the need to understand implementation-specific
    details.
  - IM classes are no longer tied to :mod:`pandasdmx.reader` instances and can
    be created and manipulated outside of a read operation.

- :mod:`pandasdmx.api` and :mod:`pandasdmx.remote` are reimplemented to (1)
  match the semantics of the requests_ package and (2) be much thinner.
- Data sources are modularized in :class:`~.source.Source`.

  - Idiosyncrasies of particular data sources (e.g. ESTAT's process for large
    requests) are handled by source-specific subclasses. As a result,
    :mod:`pandasdmx.api` is leaner.

- Test coverage has been significantly expanded.

  - There are tests for each data source (:file:`tests/test_sources.py``) to ensure the package can handle idiosyncratic behaviour.
  - The pytest-remotedata_ pytest plugin allows developers and users to run or
    skip network tests with `--remote-data`.

.. _typing: https://docs.python.org/3/library/typing.html
.. _pydantic: https://pydantic-docs.helpmanual.io
.. _requests: http://docs.python-requests.org
.. _pytest-remotedata: https://github.com/astropy/pytest-remotedata

Breaking changes
::::::::::::::::
- Python 3.6 and earlier (including Python 2) are not supported.
- various API changes. E.g., :meth:`pandasdmx.message.Message.write` is deprecated. 
  Use :func:`to_pandas` or :meth:`pandasdmx.message.Message.to_pandas` instead.
  - The layout of generated pandas objects may differ from that in v0.9.
  
Migrating from v0.9
:::::::::::::::::::::::

v1.0 include many code-breaking changes. Most notably, the default layout of pandas objects generated by pandaSDMX differs from v0.9 (see be.ow). 
Moreover, core modules including the SDMX information model were rewritten almost from scratch. The main benefit of this overhaul is the complete separation of file readers and the model-level representation of a received SDMX message. The main drawback is a severe performance hit. While up to  v0.9, the model representation was  built lazily, and some SDMX features were not supported due to certain pragmatic design choices, v1.x strives  to translate  the information contained in a given SDMX-ML or SDMX-JSON file entirely as instances of model classes. As a result, reading   a largeSDMX message may take about 30 times longer than with v0.9. On the other hand, the pandas writer is  considerably  faster in v1.x than in v0.9 as it generates   Series objects only, while delegating further conversions to DataFrames to the highly optimized pandaslayers. Further changes include:

- ``Writer.write(…, reverse_obs=True)``: use the standard pandas indexing approach to reverse a pd.Series: ``s.iloc[::-1]``
- odo support is no longer built-in; however, users can still register a pandaSDMX resource with odo. See the :ref:`HOWTO <howto-convert>`.
- :func:`.write_dataset`: the `parse_time` and `fromfreq` arguments are replaced by `datetime`; see the method documentation and the :ref:`walkthrough section <datetime>` for examples.

v0.9 (2018-04)
----------------------------

This version is the last tested on Python 2.x. Future versions
will be tested on Python 3.5+ only

New features
::::::::::::

* four new data providers INEGI (Mexico), Norges Bank (Norway),
  International Labour Organization (ILO) and
  and Italian statistics office (ISTAT)
* model: make Ref instances callable for resolving them, i.e. getting the referenced object
  by making a remote request if needed
* improve loading of structure-specific messages when DSD is not passed / must be requested on the fly
* process multiple and cascading content constraints as described in the Technical Guide (Chap. 6 of the SDMX 2.1 standard)
* StructureMessages and DataMessages now have properties to compute the constrained and unconstrained codelists as
  dicts of frozensets of codes. For DataMessage this is useful when ``series_keys`` was set to True when making
  the request. This prompts the data provider to generate a dataset without data, but with
  the complete set of series keys. This is the most accurate representation
  of the available series. Agencies such as IMF and ECB support this feature.

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


v0.9 (2018-04)
--------------

This version is the last tested on Python 2.x. Future versions will be tested on Python 3.5+ only

New features
:::::::::::::::

* four new data providers INEGI (Mexico), Norges Bank (Norway),
  International Labour Organization (ILO) and
  and Italian statistics office (ISTAT)
* model: make Ref instances callable for resolving them, i.e. getting the referenced object
  by making a remote request if needed
* improve loading of structure-specific messages when DSD is not passed / must be requested on the fly
* process multiple and cascading content constraints as described in the Technical Guide (Chap. 6 of the SDMX 2.1 standard)
* StructureMessages and DataMessages now have properties to compute the constrained and unconstrained codelists as
  dicts of frozensets of codes. For DataMessage this is useful when ``series_keys`` was set to True when making
  the request. This prompts the data provider to generate a dataset without data, but with
  the complete set of series keys. This is the most accurate representation
  of the available series. Agencies such as IMF and ECB support this feature.

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
-------------------

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


v0.2.0 (2015-04-13)
-------------------

This version is a quantum leap. The whole project has been redesigned and rewritten from
scratch to provide robust support for many SDMX features. The new architecture is centered around
a pythonic representation of the SDMX information model. It is extensible through readers and writers
for alternative input and output formats.
Export to pandas has been dramatically improved. Sphinx documentation
has been added.

v0.1.2 (2014-09-17)
-------------------

* fix xml encoding. This brings dramatic speedups when downloading and parsing data
* extend description.rst


v0.1 (2014-09)
--------------

* Initial release
