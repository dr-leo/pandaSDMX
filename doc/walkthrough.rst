Walkthrough
***********

This page walks through an example pandaSDMX workflow, providing explanations of some SDMX concepts along the way.
See also :doc:`resources`, :doc:`HOWTOs <howto>` for miscellaneous tasks, and follow links to the :doc:`glossary` where some terms are explained.

.. todo:: Maybe incorporate the following narrative sentences that were formerly in :doc:`implementation`:

   “Typical uses for attributes are the level of confidentiality, or data quality.”

   “For example, a constraint may reflect the fact that in a certain country there are no lakes or hospitals, and hence no data about water quality or hospitalization.”

   “Explore the returned :class:`.Message` instance (see :ref:`implementation notes <impl-messages>`)”

.. contents::
   :local:
   :backlinks: none


SDMX workflow
=============

Working with statistical data often includes some or all of the following steps.
:mod:`pandaSDMX` builds on SDMX features to make the steps straightforward:

1. Choose a data provider.
      :mod:`pandaSDMX` provides a built-in list of :doc:`sources`.
2. Investigate *what data is available*.
      Using :mod:`pandaSDMX`, download the catalogue of data flows available from the data provider and select a data flow for further inspection.
3. Understand *what form* the data comes in.
      Using :mod:`pandaSDMX`, download structure and metadata on the selected data flow and the data it contains, including the data structure definition, concepts, codelists and content constraints.
4. Decide *what data is required*.
      Using :mod:`pandaSDMX`, analyze the structural metadata, by directly inspecting objects or converting them to :mod:`pandas` types.
5. Download the actual data.
      Using :mod:`pandaSDMX`, specify the needed portions of the data from the data flow by constructing a selection ('key') of series and a period/time range.
      Then, retrieve the data using :meth:`Request.get`.
6. Analyze or manipulate the data.
      Convert to :mod:`pandas` types using :func:`pandasmdx.to_pandas` and use the result in further Python code and scripts.


Choose and connect to an SDMX web service
=========================================

First, we instantiate a :class:`.pandasdmx.Request` object, using the string ID of a :doc:`data source <sources>` recognized by :mod:`pandaSDMX`:

.. ipython:: python

    import pandasdmx as sdmx
    ecb = sdmx.Request('ECB')

The object ``ecb`` is now ready to make multiple data and metadata queries to the European Central Bank's web service.
To send requests to multiple web services, we could instantiate multiple :class:`Requests <.Request>`.

Configure the HTTP connection
-----------------------------

:mod:`pandaSDMX` builds on the widely-used :mod:`requests` Python HTTP library.
To pre-configure all queries made by a :class:`.Request`, we can pass any of the keyword arguments recognized by :func:`requests.request`.
For example, a proxy server can be specified:

.. ipython:: python

    ecb_via_proxy = sdmx.Request(
        'ECB',
        proxies={'http': 'http://1.2.3.4:5678'}
    )

The :attr:`~.Request.session` attribute is a :class:`.Session` object that can be used to inspect and modify configuration between queries:

.. ipython:: python

    ecb_via_proxy.session.proxies

For convenience, :attr:`~.Session.timeout` stores the timeout in seconds for HTTP requests, and is passed automatically for all queries.

Cache HTTP responses
--------------------

.. versionadded:: 0.3.0

If :mod:`requests_cache <requests_cache.core>` is installed, it is used automatically by :class:`.Session`.
To configure it, we can pass any of the arguments accepted by :class:`requests_cache.core.CachedSession` when creating a :class:`.Request`.
For example, to force :mod:`requests_cache <requests_cache.core>` to use SQLite to store cached data with the ``fast_save`` option, and expire cache entries after 10 minutes:

.. ipython:: python

    ecb_with_cache = sdmx.Request(
        'ECB',
        backend='sqlite',
        fast_save=True,
        expire_after=600,
    )

Load messages from file
-----------------------

:func:`.read_sdmx` can be used to load SDMX messages stored in local files:

.. ipython:: python

    sdmx.read_sdmx('saved_message.xml')


Obtain and explore metadata
===========================

This section illustrates how to download and explore metadata.
Suppose we are looking for time-series on exchange rates, and we know that the European Central Bank provides a relevant :term:`data flow`.

.. sidebar:: What is a data flow?

   SDMX allows that multiple data providers might publish, at different times, data points about the same measure, with the same dimensions, units, etc. For instance, two different countries might each publish their own exchange rates with a third country.

   These individual releases are called 'data sets'; the whole collection of similarly-structured data sets is a 'data flow'.

   When using SDMX web services, a request for data from a data flow with a certain ID will yield one or more data sets with observations that match the query parameters.

We *could* search the Internet for the dataflow ID or browse the ECB's website.
However, we can also use :mod:`pandaSDMX` to retrieve metadata and get a complete overview of the dataflows the ECB provides.

Getting the dataflow and related metadata
-----------------------------------------

We use :mod:`pandaSDMX` to download the definitions for all data flows available from our chosen source.
We could call :meth:`.Request.get` with ``[resource_type=]'dataflow'`` as the first argument, but can also use a shorter alias:

.. ipython:: python

    flow_msg = ecb.dataflow()

The query returns a :class:`.Message` instance.
We can also see the URL that was queried and the response headers by accessing the :attr:`.Message.response` attribute:

.. ipython:: python

   flow_msg.response.url
   flow_msg.response.headers

All the content of the response—SDMX data and metadata objects—has been parsed and is accessible from ``flow_msg``.
Let's find out what we have received:

.. ipython:: python

   flow_msg

The string representation of the Message shows us a few things:

- This is a Structure-, rather than DataMessage.
- It contains 67 :class:`.DataflowDefinition` objects.
  Because we didn't specify an ID of a particular data flow, we received the definitions for *all* data flows available from the ECB web service.
- The first of these have ID attributes like 'AME', 'BKN', …

We could inspect these each individually using :attr:`.StructureMessage.dataflow` attribute, a :class:`.DictLike` object that allows attribute- and index-style access:

.. ipython:: python

   flow_msg.dataflow.BOP

Convert metadata to :class:`pandas.Series`
------------------------------------------

However, an easier way is to use :func:`.pandasdmx.to_pandas` to convert some of the information to a :class:`pandas.Series`:

.. ipython:: python

    dataflows = sdmx.to_pandas(flow_msg.dataflow)
    dataflows.head()
    len(dataflows)

:func:`.to_pandas` accepts most instances and Python collections of :mod:`pandasdmx.model` objects, and we can use keyword arguments to control how each of these is handled.
See the method documentation for detailed.

As we are interested in exchange rate data, let's use built-in Pandas methods to choose an appropriate data flow:

.. ipython:: python

   dataflows[dataflows.str.contains('exchange', case=False)]

We decide to look at 'EXR'.

Some agencies, including ECB and INSEE, offer categorizations of data flows to help with this step.
See :ref:`this HOWTO entry <howto-categoryscheme>`.

Extract the metadata related to a data flow
-------------------------------------------

We will download the data flow definition with the ID 'EXR' from the European Central Bank.
This data flow definition is already contained in the ``flow_msg`` we retrieved with the last query, but without the data structure or any related metadata.
Now we will pass the data flow ID 'EXR', which prompts :mod:`pandaSDMX` to set the ``references`` query parameter to 'all'.
The ECB SDMX service responds by returning all metadata related to the dataflow:

.. ipython:: python

    # Here we could also use the object we have in hand:
    # exr_msg = ecb.dataflow(resource=flow_msg.dataflow.EXR)
    exr_msg = ecb.dataflow('EXR')
    exr_msg.response.url

    # The response includes several classes of SDMX objects
    exr_msg

    exr_flow = exr_msg.dataflow.EXR

The :attr:`.DataflowDefinition.structure` attribute refers to the data structure definition (DSD, an instance of :class:`.DataStructureDefinition`).
As the name implies, this object contains metadata that we can use to explore the structure of data from the 'EXR' flow:

.. ipython:: python

    # Show the data structure definition referred to by the data flow
    dsd = exr_flow.structure
    dsd

    # The same object instance is accessible from the StructureMessage
    dsd is exr_msg.structure.ECB_EXR1

Among other things, the DSD defines:

- the order and names of the :class:`Dimensions <.Dimension>`, and the allowed values, data type or codes for each dimension, and
- the names, allowed values, and valid points of attachment for :class:`DataAttributes <.DataAttribute>`.
- the :class:`.PrimaryMeasure`, i.e. a description of the thing being measured by the observation values.

.. ipython:: python

    # Explore the DSD
    dsd.dimensions.components
    dsd.attributes.components
    dsd.measures.components

Chosing just the 'FREQ' dimension, we can explore the :class:`.CodeList` that contains valid values for this dimension in the data flow:

.. ipython:: python

    # Show a codelist referenced by a dimension, containing a superset
    # of existing values
    cl = dsd.dimensions.get('FREQ').local_representation.enumerated
    cl

    # Again, the same object can be accessed directly
    cl is exr_msg.codelist.CL_FREQ

    # Convert to a pandas.Series to see more information
    sdmx.to_pandas(cl)


Understand constraints
----------------------

The 'CURRENCY' and 'CURRENCY_DENOM' dimensions of this DSD share the same 'CL_CURRENCY' code list.
In order to be reusable for as many data sets as possible, this code list is extensive and complete:

.. ipython:: python

    len(exr_msg.codelist.CL_CURRENCY)

However, the *European* Central Bank does not, in its 'EXR' data flow, commit to providing exchange rates between—for instance—the Congolose franc ('CDF') and Peruvian sol ('PEN').
In other words, the values of ('CURRENCY', 'CURRENCY_DENOM') that we can expect to find in 'EXR' is much smaller than the 359 × 359 possible combinations of two values from 'CL_CURRENCY'.

How much smaller?
Let's return to explore the :class:`.ContentConstraint` that came with our metadata query:

.. ipython:: python

    exr_msg.constraint.EXR_CONSTRAINTS

    # Get the content 'region' included in the constraint
    cr = exr_msg.constraint.EXR_CONSTRAINTS.data_content_region

    # Get the valid members for two dimensions
    c1 = sdmx.to_pandas(cr.member['CURRENCY'].values)
    len(c1)

    c2 = sdmx.to_pandas(cr.member['CURRENCY_DENOM'].values)
    len(c2)

    # Explore the contents
    # Currencies that are valid for CURRENCY_DENOM, but not CURRENCY
    c2 - c1
    # The opposite:
    c1 - c2

    # Check certain contents
    {'CDF', 'PEN'} < c1 | c2
    {'USD', 'JPY'} < c1 & c2

We see that 'USD' and 'JPY' are valid values along both dimensions.

Attribute names and allowed values can be obtained in a similar fashion.


Select and request data from a dataflow
=======================================

Next, we will obtain some data.

.. todo:: Edit text below this point to:

   - Refer to the documentation of methods, parameters, etc., instead of repeating it.
   - Reduce repetition, including of things described both here and in :doc:`implementation`.
   - Eliminate descriptions/justifications of removed workarounds.
   - Avoid repeating descriptions of SDMX, the IM, etc. that are provided more clearly by other sources; link to them instead.

Requesting a dataset is as easy as requesting a dataflow definition or any other SDMX artefact: just call :meth:`.Request.get` and pass it 'data' as the resource_type and the dataflow ID as resource_id.
As a shortcut, you can use the ``data`` descriptor which calls the ``get`` method implicitly.

Generic or structure-specific data format?
------------------------------------------

Data providers which support SDMX-ML offer data sets in two distinct formats:

- generic data sets: These are self-contained but less memory-efficient.
  They are suitable for small to medium data sets, but less so for large ones.
- Structure-specific data sets: This format is memory-efficient (typically about 60 per cent smaller than a generic data set) but it requires the datastructure definition (DSD) to interpret the XML file.
  The DSD must be downloaded prior to parsing the dataset.
  pandaSDMX can do this behind the scenes.
  However, as we shall see in the next section, the DSD can also be provided by the caller to save an additional request.

The intended data format is chosen by selecting the agency.
For example, 'ECB' provides generic data sets, whereas 'ECB_S' provides structure-specific data sets.
Hence, there are actually two agency ID's for ECB, ESTAT etc.
Note that data providers supporting SDMXJSON only work with a single format for data sets.
Hence, there is merely one agency ID for OECD and ABS.

Filtering
---------

In most cases we want to filter the data by columns or rows in order to request only the data we are interested in.
Not only does this increase performance.
Rather, some dataflows are really huge, and would exceed the server or client limits.
The REST API of SDMX offers two ways to narrow down a data request:

- specifying dimension values which the series to be returned must match (filtering by column labels), or
- limiting the time range or number of observations per series (filtering by row labels)

From the ECB's dataflow on exchange rates, we specify the CURRENCY dimension to be either 'USD' or 'JPY'.
This can be done by passing a ``key``  keyword argument to the ``get``  method or the ``data`` descriptor.
It may either be a string (low-level API) or a dict.
The dict form introduced in v0.3.0 is more convenient and pythonic as it allows pandaSDMX to infer the string form from the dict.
Its keys (= dimension names) and values (= dimension values) will be validated against the datastructure definition as well as the content-constraint if available.

Content-constraints are implemented only in their CubeRegion flavor.
KeyValueSets are not yet supported.
In this case, the provided demension values will be validated only against the unconstrained codelist.
It is thus not always guaranteed that the dataset actually contains the desired data, e.g., because the country of interest does not deliver the data to the SDMX data provider.
Note that even constrained codelists do not guarantee that for a given key there will be data on the server.
This is because the codelists may mislead the user to think that every element of their cartesian product is a valid key for a series, whereas there is actually data merely for a subset of that product.
The KeyValue flavor of content constraints is thus a more accurate predictor.
But this feature is not known to be used by any data provider.
Thus pandaSDMX does not support it.

Another way to validate a key against valid codes are series-key-only datasets, i.e. a dataset with all possible series keys where no series contains any observation.
pandaSDMX supports this validation method as well.
However, it is disabled by default.
Pass ``series_keys=True`` to the Request method to validate a given key against a series-keys only dataset rather than the DSD.

If we choose the string form of the key, it must consist of '.'-separated slots representing the dimensions.
Values are optional.
As we saw in the previous section, the ECB's dataflow for exchange rates has five relevant dimensions, the 'CURRENCY' dimension being at position two.
This yields the key '.USD+JPY...'.
The '+' can be read as an 'OR' operator.
The dict form is shown below.

Further, we will set a meaningful start period for the time series to exclude any prior data from the request.

To request the data in generic format, we could simply issue:

.. ipython:: python

    data_msg = ecb.data(
        resource_id='EXR',
        key={'CURRENCY': ['USD', 'JPY']},
        params={'startPeriod': '2016'})
    data = data_msg.data[0]
    type(data)

However, we want to demonstrate how structure-specific data sets are requested.
To this end, we instantiate a one-off Request object configured to make requests for efficient structure-specific data, and we pass it the DSD obtained in the previous section.
Without passing the DSD, it would be downloaded automatically right after the data set:

.. ipython:: python
   :okexcept:

    data_msg = sdmx.Request('ecb_s').data(
        resource_id='EXR',
        key={'CURRENCY': ['USD', 'JPY']},
        params={'startPeriod': '2017'}, dsd=dsd)
    data = data_msg.data[0]
    type(data)

Data sets
---------

This section explains the key elements and structure of datasets.
You can skip it on first read when you just want to be able to download data and export it to pandas.
More advanced operations, e.g., exporting only a subset of series to pandas, requires some understanding of the anatomy of a dataset including observations and attributes.

As we saw in the previous section, the datastructure definition (DSD) is crucial to understanding the data structure, the meaning of dimension and attribute values, and to select series of interest from the entire dataset by specifying a valid key.

The :class:`pandasdmx.model.DataSet` class has the following features:

``dim_at_obs``
    attribute showing which dimension is at observation level.
    For time series its value is either 'TIME' or 'TIME_PERIOD'.
    If it is 'AllDimensions', the dataset is said to be flat.
    In this case there are no series, just a flat list of observations.
series
    property returning an iterator over :class:`pandasdmx.model.Series` instances
obs
    method returning an iterator over the observations.
    Only for flat datasets.
attributes
    namedtuple of attributes, if any, that are attached at dataset level.


The :class:`pandasdmx.model.Series` class has the following features:

key
    nnamedtuple mapping dimension names to dimension values
obs
    method returning an iterator over observations within the series
attributes:
    namedtuple mapping any attribute names to values
groups
    list of :class:`pandasdmx.model.Group` instances to which this series
    belongs.
    Note that groups are merely attachment points for attributes.

.. ipython:: python
   :okexcept:

    data.dim_at_obs
    len(data.series)
    list(data.series.keys())[5]
    set(series_key.FREQ for series_key in data.series.keys())

This dataset thus comprises 16 time series of several different period lengths.
We could have chosen to request only daily data in the first place by providing the value ``D`` for the ``FREQ`` dimension.
In the next section we will show how columns from a dataset can be selected through the information model when writing to a pandas DataFrame.

Convert data to pandas
======================

Select columns using the model API
----------------------------------

As we want to write data to a pandas DataFrame rather than an iterator of pandas Series, we avoid mixing up different frequencies as pandas may raise an error when passed data with incompatible frequencies.
Therefore, we single out the series with daily data.
The :meth:`pandasdmx.api.Response.write` method accepts an optional iterable to select a subset of the series contained in the dataset.
Thus we can now generate our pandas DataFrame from daily exchange rate data only:

.. ipython:: python

    import pandas as pd
    daily = [s for sk, s in data.series.items() if sk.FREQ == 'D']
    cur_df = pd.concat(sdmx.to_pandas(daily))
    cur_df.shape
    cur_df.tail()

Control the output
------------------

See :func:`.write_dataset`.

Work with files
===============

The :meth:`pandasdmx.api.Request.get` method accepts two optional keyword arguments ``tofile``  and ``fromfile``.
If a file path or, in case of ``fromfile``, a  file-like object is given, any SDMX message received from the server will be written to a file, or a file will be read instead of making a request to a remote server.

.. versionadded:: 0.2.1

The file to be read may be a zip file.
In this case, the SDMX message must be the first file in the archive.
The same works for zip files returned from an SDMX server.
This happens, e.g., when Eurostat finds that the requested dataset has been too large.
In this case the first request will yield a message with a footer containing a link to a zip file to be made available after some time.
The link may be extracted by issuing something like:

    >>> resp.footer.text[1]

and passed as ``url`` argument when calling ``get`` a second time to get the zipped data message.

This second request can be performed automatically through the ``get_footer_url`` parameter.
It defaults to ``(30, 3)`` which means that three attempts will be made in 30 seconds intervals.
This behavior is useful when requesting large datasets from Eurostat.
Deactivate it by setting ``get_footer_url`` to None.

You can use :meth:`pandasdmx.api.Response.write_source` to save the serialized XML tree to a file.

.. versionadded:: 0.4

Cache Response instances in memory
==================================

The ''get'' API provides a rudimentary cache for Response instances.
It is a simple dict mapping user-provided names to the Response instances.
If we want to cache a Response, we can provide a suitable name by passing the keyword argument ``memcache`` to the get method.
Pre-existing items under the same key will be overwritten.

.. note::

   Caching of http responses can also be achieved through ''requests-cache'.
   Activate the cache by instantiating :class:`pandasdmx.api.Request` passing a keyword argument ``cache``.
   It must be a dict mapping config and other values.


Handle errors
=============

The :class:`pandasdmx.api.Response` instance generated upon receipt of the response from the server has a ``status_code``  attribute.
The SDMX web services guidelines explain the meaning of these codes.
In addition, if the SDMX server has encountered an error, it may return a message which includes a footer containing explanatory notes.
pandaSDMX exposes the content of a footer via a ``text`` attribute which is a list of strings.

.. note::

   pandaSDMX raises only http errors with status code between 400 and 499.
   Codes >= 500 do not raise an error as the SDMX web services guidelines define special meanings to those codes.
   The caller must therefore raise an error if needed.
