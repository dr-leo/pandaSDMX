.. _agencies:    
    
Data providers
=========================================


Overview
-----------

pandaSDMX supports a number of data providers out of the box. Each data provider
is configured by an item in ``agencies.json`` in the package root. Data providers are
identified by a case-insensitive string such as "ECB", "ESTAT_S" or "OECD". For each pre-configured data provider, ``agencies.json`` contains
the URL and name of the SDMX API and potentially some additional
metadata about the provider's web API. The configuration information about data
providers is stored in the dict-type class attribute ``_agencies`` of :class:`Request`.
Other data providers can be configured by passing a suitable json-file to the
:meth:`pandasdmx.api.Request.add_agency` method which will be used to update the dict
storing the agency configuration. 
  

Pre-configured data providers
-----------------------------------

This section describes the data providers supported
out of the box. The most salient distinction
between data providers derives from the supported API: While OECD and
Australian Bureau of Statistics (ABS) are only supported with regards to their SDMX-JSON APIs, all others
send SDMX-ML messages. SDMX-JSON is currently confined to
data messages. Hence, pandaSDMX features relating to
structural metadata are unavailable when making requests to OECD or ABS.

Agencies supporting SDMXML messages come in two flavors: one for
generic data sets (e.g. ECB, ESTAT, INSEE etc.), the other for structure-specific data sets (e.g., ECB_S, ESTAT_S etc.).


`Australian Bureau of Statistics (ABS) <http://www.abs.gov.au/>`_
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
SDMX-JSON only. Start by browsing the website to retrieve the dataflow you're interested in.
Then try to fine-tune a planned data request by providing a valid key (= selection of series from the dataset). 
No automatic validation
can be performed as structural metadata is unavailable.

  
`Eurostat <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`_
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

* SDMXML-based API. 
* thousands of dataflows on a wide range of topics.
* No categorisations available.
* Long response times are reported. Increase the timeout attribute to avoid timeout exceptions.

`European Central Bank (ECB) <http://www.ecb.europa.eu/stats/ecb_statistics/co-operation_and_standards/sdmx/html/index.en.html>`_
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
* SDMXML-based API
* supports categorisations of data-flows
* supports preview_data and series-key based key validation
* in general short response times 

`French National Institute for Statistics (INSEE) <http://www.bdm.insee.fr/bdm2/statique?page=sdmx>`_
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  
  * SDMXML-based API.
  
  
`International Monetary Fund (IMF) - SDMX Central only <https://sdmxcentral.imf.org/>`_
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

* SDMXML-based API
* subset of the data available on http://data.imf.org   
     * full IMF data access would require SOAP API support. This feature needs to be added.
     
     
`Organisation for Economic Cooperation and Development (OECD) <http://stats.oecd.org/SDMX-JSON/>`_
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
SDMX-JSON only. Start by browsing the website to retrieve the dataflow you're interested in.
Then try to fine-tune a planned data request by providing a valid key (= selection of series from the dataset). 
No automatic validation
can be performed as structural metadata is unavailable.

  
`United Nations Statistics Division (UNSD) <https://unstats.un.org/home/>`_
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
* SDMXML-based API
* supports preview_data and series-key based key validation


`UNESCO <https://apiportal.uis.unesco.org/getting-started>`_ 
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
* free registration required
* subscription key must be provided either as parameter or HTTP-header with each request   
* SDMXML-based API
 
 
`World Bank - World Integrated Trade Solution (WBG_WITS) <wits.worldbank.org>`_
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

* SDMX-ML-based API.

