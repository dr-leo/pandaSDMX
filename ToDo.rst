pandaSDMX - ToDo
===================


1. SDMX support
--------------------

In v0.1, only a fraction of the SDMX standards is supported. v2.0 support is experimental. 
Eurostat works quite well though. 
 
1.1 data acquisition
~~~~~~~~~~~~~~

* data: observation status and observation flags are ignored. Decide how best to
  get these into DataFrames. Option 1: Generate a separate df with identical column index 
  for obs_status. Option 2: add a new index level to distinguish data and obs_status so as to
  add a column for obs_status next to each data column
* datatypes: currently, all data is converted to float64. Infer other dypes and make
  conversion configurable. Handle categorical data if any
* handle non-time series data

   1.2 dataflows
   ~~~~~~~~~~~~~~
   
   * in v0.1, categories are ignored. 
* ECB: flowrefs are not unique. Do categories solve this problem?
  There are 46 unique dataflows and 666 dataflows returned. Titles are often identical.
  Do not understand this. Maybe categories will solve this problem. But a flowref does not uniquely identify
  a dataset. Call get_data() differently? Need to better understand SDMX 2.0 to
  solve this problem.

   
   1.3 Web service / http
   ~~~~~~~~~~~~~~~
   
   * in v0.1, only Eurostats works well. FAO, ILO etc. cause errors.
* either generalize Client.request() or subclass Client for providers other than Eurostat.
* use WADL and/or WSDL to make requests according to the service's properties

2. pandas output
--------------------

* construct datetime index specifying freq or reindex with asfreq()
    
   
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


