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


.. _ESTAT:

``ESTAT``: Eurostat
-------------------

SDMX-ML —
`Website <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`__

- Thousands of dataflows on a wide range of topics.
- No categorisations available.
- Long response times are reported. Increase the timeout attribute to avoid
  timeout exceptions.

.. autoclass:: pandasdmx.source.estat.Source
   :members:


``ECB``: European Central Bank
------------------------------

SDMX-ML —
`Website <http://www.ecb.europa.eu/stats/ecb_statistics/co-operation_and_standards/sdmx/html/index.en.html>`__

- Supports categorisations of data-flows.
- Supports preview_data and series-key based key validation.
- In general short response times.


``ILO``: International Labour Organization
------------------------------------------

SDMX-ML —
`Website <www.ilo.org/ilostat/>`__

- :class:`pandasdmx.source.ilo.Source` handles some particularities of the ILO
  web service. Others that are not handled:

  - Data flow IDs take on the role of a filter. E.g., there are dataflows for
    individual countries, ages, sexes etc. rather than merely for different
    indicators.
  - The service returns 413 Payload Too Large errors for some queries, with
    messages like: "Too many results, please specify codelist ID". Test for
    :class:`pandasdmx.exceptions.HTTPError`
    (= :class:`requests.exceptions.HTTPError`) and/or specify a ``resource_id``.

- It is highly recommended to read the `API guide <http://www.ilo.org/ilostat/content/conn/ILOSTATContentServer/path/Contribution%20Folders/statistics/web_pages/static_pages/technical_page/ilostat_appl/SDMX_User_Guide.pdf>`_.

.. autoclass:: pandasdmx.source.ilo.Source
   :members:


.. _IMF:

``IMF``: International Monetary Fund's “SDMX Central” source
------------------------------------------------------------

SDMX-ML —
`Website <https://sdmxcentral.imf.org/>`__

- Subset of the data available on http://data.imf.org.
- Supports series-key-only and hence dataset-based key validation and construction.


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


``NB``: Norges Bank (Norway)
----------------------------

SDMX-ML —
`Website <https://www.norges-bank.no/en/topics/Statistics/open-data/>`__

- Few dataflows. So do not use categoryscheme.
- It is unknown whether NB supports series-keys-only.


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


``UNSD``: United Nations Statistics Division
--------------------------------------------

SDMX-ML —
`Website <https://unstats.un.org/home/>`__

- Supports preview_data and series-key based key validation.

.. warning:: supports categoryscheme even though it offers very few dataflows.  Use this feature with caution. Moreover, it seems that categories confusingly
  include dataflows which UNSD does not actually provide.


``UNESCO``: UN Educational, Scientific and Cultural Organization
----------------------------------------------------------------

SDMX-ML —
`Website <https://apiportal.uis.unesco.org/getting-started>`__

- Free registration required; user credentials must be provided either as
  parameter or HTTP header with each request.

.. warning:: An issue with structure-specific datasets has been reported.
  It seems that Series are not recognized due to some oddity
  in the XML format.


``WB``: World Bank Group's “World Integrated Trade Solution”
------------------------------------------------------------

SDMX-ML —
`Website <wits.worldbank.org>`__
