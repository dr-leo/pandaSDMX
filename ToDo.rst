pandaSDMX - ToDo
===================


1. SDMX support
--------------------

In v0.1, only a fraction of the SDMX standards is supported. v2.0 support is experimental. 
Eurostat works quite well though. 
 
1.1 get_data 
~~~~~~~~~~~~~~

* data: observation status and observation flags are ignored. Decide how best to
  expose these as DataFrames. Option 1: Generate a separate df with identical column index 
  for obs_status. Option 2: add a new index level to distinguish data and obs_status so as to
  add a column for obs_status next to each data column
* datatypes: currently, all data is converted to float64. Infer other dypes and make
  conversion configurable. Handle categorical data if any
* handle non-time series data
* handle mixed-frequency data: return a list of DataFrames rather than trying to 
  coerce them into one. Allow to specify thru concat arg a key such as GEO whose values will 
  make a dataframe.
  * keys (= filter data by code value): abolish the '...DE' syntax. Use
  kwargs instead. Validate them using content constraints (= dataset-specific codes)


1.2 get_codes
   ~~~~~~~~~

The order of keys in the OrderedDict returned by the get_codes method
does not correspond to the actual order required to construct the 'key' string
to pas to the get_data method as second argument. Find out why and how to fix it.
Do we have to request the list of keys in correct order separately?


Add attribute syntax by subclassing OrderedDict. Or is that possible already?

* add get_constraints method for the list of codes used by a specified dataset (without
natural language description which are only contained in code_lists
* add feature to request items from an item scheme. Do not quite understand this yet.

   1.3 get_dataflows
   ~~~~~~~~~~~~~~
   
   * add feature: Get categories and make table of dategories in the database 
   * get categorizations linking dataflows to categories

   
   1.4 Web service / http
   ~~~~~~~~~~~~~~~
   
   * in v0.1, only Eurostats works well. FAO, ILO etc. cause errors.
* either generalize Client.request() or subclass Client for providers other than Eurostat.
* use WADL and/or WSDL to make requests according to the service's properties
* consider RESTful client libs such as docar, wac or alfresco, restclient,
  py-restclient, drest (sounds good).  

2. pandas output
--------------------

* handle mixed-frequency data.
    handle non-timeseries data
    attach global metadata to df rather than as separate dict
    handle obs_status etc.
    
   
    3. Database support
    --------------------------
    
    * use other databases with sqlalchemy
    * store categories in separate tables with foreign key relations 
  * add column to dataflows table specifying alternative location such as local file
  

4. Docs
------------

* add docs using Sphinx and ipython directive

5. Testing
-----------

* add meaningful unittests


