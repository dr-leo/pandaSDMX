.. currentmodule:: pandasdmx

Data sources
============

SDMX makes a distinction between data providers and sources:

- a **data provider** is the original publisher of statistical information and
  metadata.
- a **data source** is a specific web service that provides access to
  statistical information.

Each data *source* might aggregate and provide data or metadata from multiple
data *providers*. Or, an agency might operate a data source that only contains
information they provide themselves; in this case, the source and provider are
identical.

pandaSDMX identifies each data source using a string such as ``'ABS'``, and has
built-in support for a number of data sources. Use :meth:`list_sources` to list
these. Read the following sections, or the file ``sources.json`` in the
package source code, for more details.

pandaSDMX also supports adding other data sources; see :meth:`add_source` and :class:`~.source.Source`.

.. contents::
   :local:
   :backlinks: none


Data source limitations
-----------------------

Each SDMX web service provides a subset of the full SDMX feature set, so the
same request made to two different sources may yield different results, or an
error message.

A key difference is between sources offering SDMX-ML and SDMX-JSON APIs.
SDMX-JSON APIs do not support metadata, or structure queries; only data queries.

.. note:: For JSON APIs, start by browsing the source's website to retrieve the dataflow you're interested in. Then try to fine-tune a planned data request by providing a valid key (= selection of series from the dataset).
   Because structure metadata is unavailable, :mod:`pandaSDMX` cannot automatically validate keys.

In order to anticipate and handle these differences:

1. :meth:`add_source` accepts "data_content_type" and "supported" keys. For
   example:

   .. code-block:: json

      [
        {
          "id": "ABS",
          "data_content_type": "JSON"
        },
        {
          "id": "UNESCO",
          "unsupported": ["datastructure"]
        },
      ]

   pandaSDMX will raise :class:`NotImplementedError` on an attempt to query the
   "datastructure" API endpoint of either of these data sources.

2. :mod:`pandasdmx.source` includes adapters (subclasses of
   :class:`~.source.Source`) with hooks used when querying sources and
   interpreting their HTTP responses.
   These are documented below: ABS_, ESTAT_, and SGR_.


.. _ABS:

``ABS``: Australian Bureau of Statistics
----------------------------------------

SDMX-JSON —
`Website <http://www.abs.gov.au/>`__

.. autoclass:: pandasdmx.source.abs.Source
   :members:


.. _BIS:

``BIS``: Bank for International Settlements
---------------------------------------------

SDMX-ML —
`Website <https://stats.bis.org/api-doc/v1/>`__

-  service went live  in  April 2021
- Supports preview_data and series-key based key validation.



``ECB``: European Central Bank
------------------------------

SDMX-ML —
`Website <http://www.ecb.europa.eu/stats/ecb_statistics/co-operation_and_standards/sdmx/html/index.en.html>`__

- Supports categorisations of data-flows.
- Supports preview_data and series-key based key validation.
- In general short response times.



.. _ESTAT:

``ESTAT``: Eurostat
-------------------

SDMX-ML —
`Website <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`__

- Thousands of dataflows on a wide range of topics.
- No categorisations available.
- Long response times are reported. Increase the timeout attribute to avoid
  timeout exceptions.
- Does not return DSDs for dataflow requests with the ``references='all'`` query parameter.

.. autoclass:: pandasdmx.source.estat.Source
   :members:


``ILO``: International Labour Organization
------------------------------------------

SDMX-ML —
`Website <www.ilo.org/ilostat/>`__

The ILO SDMX web service API has been updated in  2020.
The adapter shipped with pandasdmx until v1.3.0
is now counterproductive and has been removed in v1.3.1.  

  - Data flow IDs take on the role of a filter. E.g., there are dataflows for
    individual countries, ages, sexes etc. rather than merely for different
    indicators.

- It is highly recommended to read the `User guide <https://www.ilo.org/ilostat-files/Documents/SDMX_User_Guide.pdf>`_.



.. _IMF:

``IMF``: International Monetary Fund's “SDMX Central” source
------------------------------------------------------------

SDMX-ML —
`Website <https://sdmxcentral.imf.org/>`__

- The SDMX REST API no longer accepts data queries. But queries for metadata still work.
  Datasets must be retrieved manually from 
  https://data.imf.org.  


``INEGI``: National Institute of Statistics and Geography (Mexico)
------------------------------------------------------------------

SDMX-ML —
`Website <https://sdmx.snieg.mx/infrastructure>`__.

- Spanish name: Instituto Nacional de Estadística y Geografía.


``INSEE``: National Institute of Statistics and Economic Studies (France)
-------------------------------------------------------------------------

SDMX-ML —
`Website <http://www.bdm.insee.fr/bdm2/statique?page=sdmx>`__

- French name: Institut national de la statistique et des études économiques.

.. warning::
   An issue has been reported apparently due to a missing pericite codelist
   in StructureMessages. This may cause crashes. Avoid downloading
   this type of message. Prepare the key as string using the web interface, and
   simply download a dataset.


``ISTAT``: National Institute of Statistics (Italy)
---------------------------------------------------

SDMX-ML —
`Website <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`__

- Italian name: Istituto Nazionale di Statistica.
- Similar server platform to Eurostat, with similar capabilities.

``LSD``: National Institute of Statistics (Lithuania)
-----------------------------------------------------

SDMX-ML —
`Website <https://osp.stat.gov.lt/rdb-rest>`__


``NB``: Norges Bank (Norway)
----------------------------

SDMX-ML —
`Website <https://www.norges-bank.no/en/topics/Statistics/open-data/>`__

- Few dataflows. So do not use categoryscheme.
- It is unknown whether NB supports series-keys-only.

``NBB``: National Bank of Belgium 
-------------------------------------------

SDMX-JSON only. Only data queries supported. Discover 
dataflows on the website and query the required data sets.
 
`Website <https://stat.nbb.be/>`__ —
API documentation `(en) <https://www.nbb.be/doc/dq/migratie_belgostat/en/nbb_stat-technical-manual.pdf>`__

``OECD``: Organisation for Economic Cooperation and Development
---------------------------------------------------------------

SDMX-JSON —
`Website <http://stats.oecd.org/SDMX-JSON/>`__


.. _SGR:

``SGR``: SDMX Global Registry
-----------------------------

SDMX-ML —
`Website <https://registry.sdmx.org/ws/rest>`__

.. autoclass:: pandasdmx.source.sgr.Source
   :members:

``SPC``: Pacific Data Hub
----------------------------------------------------------------

SDMX-ML —
`Website <:"https://stats.pacificdata.org/?locale=en>`__
This service also offers SDMXJSON datasets. This feature requires a specific 
HTTP header as described on the website.
There seems to be an  on SPC's side
in series-key-only data messages as the reference to the DSD's is not recognizsed.


``STAT_EE``: Statistics Estonia 
-----------------------------------------

SDMX-JSON. Data queries only. No metadata. Discover dataflows through the website.
 
`Website <http://andmebaas.stat.ee>`__ (et) —
API documentation `(en) <https://www.stat.ee/sites/default/files/2020-09/API-instructions.pdf>`__, `(et) <https://www.stat.ee/sites/default/files/2020-09/API-juhend.pdf>`__


``UNSD``: United Nations Statistics Division
--------------------------------------------

SDMX-ML —
`Website <https://unstats.un.org/home/>`__

- Supports preview_data and series-key based key validation.

.. warning:: supports categoryscheme even though it offers very few dataflows.  Use this feature with caution. Moreover, it seems that categories confusingly
  include dataflows which UNSD does not actually provide.


``UNICEF``: UN International Children's Emergency Fund
----------------------------------------------------------------

SDMX-ML —
`Website <https://data.unicef.org/>`_



``CD2030``: Countdown 2030
----------------------------------------------------------------

SDMX-ML —
`Website <https://profiles.countdown2030.org/>`_



``WB``: World Bank Group's “World Integrated Trade Solution”
------------------------------------------------------------

SDMX-ML —
`Website <wits.worldbank.org>`__

``WB_WDI``: World Bank Group's “World Development Indicators”
----------------------------------------------------------------

SDMX-ML —
`Website <https://datahelpdesk.worldbank.org/knowledgebase/articles/1886701-sdmx-api-queries>`__
This service also offers SDMXJSON datasets. This feature requires a specific 
HTTP header as described on the website.
Queries for a list of dataflows do not seem to be supported.
