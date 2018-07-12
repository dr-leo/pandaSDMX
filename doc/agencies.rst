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
* An issue has been reportet apparently due to a missing pericite codelist
  in StructureMessages. This may cause crashes. Avoid downloading
  this type of message. Prepare the key as string using the web interface, and
  simply download a dataset.
  
  
`International Labour Organization (ILO) <www.ilo.org/ilostat/>`_ 
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

ILO's SDMX web API deviates in some respects from the others. It is highly recommended to
read the `API guide <http://www.ilo.org/ilostat/content/conn/ILOSTATContentServer/path/Contribution%20Folders/statistics/web_pages/static_pages/technical_page/ilostat_appl/SDMX_User_Guide.pdf>`_.   
Here are some of the gotchas:

* dataflow IDs take on the role of a filter. E.g., there are dataflows for individual countries, ages, sexes etc. rather than
  merely for different indicators.
* Do not set the 'references' parameter to 'all' as is done by pandaSDMX by default when
  one requests a dataflow specified by ID. ILO can handle 'references' = 'descendants' and 
  some others, but not 'all'.
* As the default format is SDMX 2.0, 
  the 'format' parameter should be set to 'generic_2_1' or equivalent for each request.
   
`International Monetary Fund (IMF) - SDMX Central only <https://sdmxcentral.imf.org/>`_
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

* SDMXML-based API
* supports series-key-only and hence dataset-based key validation and construction.

`Italian Statistics Office (ISTAT) <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`_
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

ISTAT uses roughly the Same server platform as Eurostat.
     
Norges Bank (Central Bank of Norway, "NB" or "NB_S")
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::     
     
* agency ID: 'NB' for generic, "NB_S" for structure-specific data
* few dataflows. So do not use categoryscheme
* it is unknown whether NB supports series-keys-only
     
     
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
* supports categoryscheme even though it offers very few dataflows. Do
  don't use this feature. Moreover, it seems that categories confusingly 
  include dataflows
  which UNSD does not actually provide.


`UNESCO <https://apiportal.uis.unesco.org/getting-started>`_ 
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
* free registration required
* subscription key must be provided either as parameter or HTTP-header with each request   
* SDMXML-based API
* An issue with structure-specific datasets has been reported.
  It seems that Series are not recognized due to some oddity
  in the XML format. 
 
 
`World Bank - World Integrated Trade Solution (WBG_WITS) <wits.worldbank.org>`_
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

* SDMX-ML-based API.

