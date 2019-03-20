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
information provided by the same agency.

pandaSDMX identifies each data source using a string such as ``ABS``, and has
built-in support for a number of data sources. Use :meth:`list_sources` to list
these. Read the following sections, or the file ``sources.json`` in the
package source code, for more details.

pandaSDMX also supports adding other data sources; see :meth:`add_source` and :class:`pandasdmx.source.Source`.

Data source limitations
-----------------------

Each SDMX web service provides a subset of the full SDMX feature set, so the
same request made to two different sources may yield different results, or an
error message.

A key difference is between sources offering SDMX-ML and SDMX-JSON APIs.
SDMX-JSON APIs do not support structure queries; only data queries.

In order to anticipate and handle these differences:

1. :meth:`add_source` accepts "data_content_type" and "unsupported" keys. For
   example:

   .. code-block:: json

       "ABS": {
           "id": "ABS",
           "data_content_type": "JSON",
           …
          },
      "UNESCO": {
          "id": "UNESCO",
          …
          "unsupported": ["datastructure"]
          },

   pandaSDMX will raise :class:`NotImplementedError` on an attempt to query the
   "datastructure" API endpoint of either of these data sources.

2. :mod:`pandasdmx.source` includes adapters (subclasses of
   :class:`pandasdmx.source.Source`) with hooks used when querying sources and
   interpreting their HTTP responses. These are documented below: ABS_, ESTAT_,
   and SGR_.


Built-in data sources
---------------------

.. todo::

   The snippets of text for each source are not current with ``sources.json``. Update, or generate automatically.

.. contents::
   :local:
   :backlinks: none

.. _ABS:

``ABS``: Australian Bureau of Statistics
::::::::::::::::::::::::::::::::::::::::

- `Website <http://www.abs.gov.au/>`__

SDMX-JSON only. Start by browsing the website to retrieve the dataflow you're
interested in. Then try to fine-tune a planned data request by providing a
valid key (= selection of series from the dataset). No automatic validation can
be performed as structural metadata is unavailable.


.. autoclass:: pandasdmx.source.abs.Source
   :members:

.. _ESTAT:

``ESTAT``: Eurostat
:::::::::::::::::::

- `Website <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`__
- SDMX-ML.
- Thousands of dataflows on a wide range of topics.
- No categorisations available.
- Long response times are reported. Increase the timeout attribute to avoid
  timeout exceptions.

.. autoclass:: pandasdmx.source.estat.Source
   :members:


``ECB``: European Central Bank
::::::::::::::::::::::::::::::

- `Website <http://www.ecb.europa.eu/stats/ecb_statistics/co-operation_and_standards/sdmx/html/index.en.html>`__
- SDMX-ML.
- Supports categorisations of data-flows.
- Supports preview_data and series-key based key validation.
- In general short response times.


``INSEE``: French National Institute for Statistics
:::::::::::::::::::::::::::::::::::::::::::::::::::

- `Website <http://www.bdm.insee.fr/bdm2/statique?page=sdmx>`__


.. _IMF:

``IMF``: International Monetary Fund's “SDMX Central” source
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

- `Website <https://sdmxcentral.imf.org/>`__
- SDMX-ML.
- Subset of the data available on http://data.imf.org.


``OECD``: Organisation for Economic Cooperation and Development
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

- `Website <http://stats.oecd.org/SDMX-JSON/>`__
- SDMX-JSON.

.. _SGR:

``SGR``: SDMX Global Registry
:::::::::::::::::::::::::::::

- `Website <https://registry.sdmx.org/ws/rest>`__
- SDMX-ML.

.. autoclass:: pandasdmx.source.sgr.Source
   :members:


``UNSD``: United Nations Statistics Division
::::::::::::::::::::::::::::::::::::::::::::

- `Website <https://unstats.un.org/home/>`__
- SDMX-ML.
- Supports preview_data and series-key based key validation.


``UNESCO``: UN Educational, Scientific and Cultural Organization
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

- `Website <https://apiportal.uis.unesco.org/getting-started>`__
- SDMX-ML.
- Free registration required; user credentials must be provided either as
  parameter or HTTP-header with each request.


``WBG_WITS``: World Bank Group's “World Integrated Trade Solution”
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

- `Website <wits.worldbank.org>`__
- SDMX-ML.
