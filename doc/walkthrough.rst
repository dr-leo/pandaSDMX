Walkthrough
***********

This page walks through an example pandaSDMX workflow, providing explanations of some SDMX concepts along the way.
See also :doc:`resources`, :doc:`HOWTOs <howto>` for miscellaneous tasks, and follow links to the :doc:`glossary` where some terms are explained.

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
     Download structure and other metadata on the selected data flow and the data it contains, including the data structure definition, concepts, codelists and content constraints.
4. Decide *what data points you need* from the dataflow.
      Analyze the structural metadata, by directly inspecting objects or converting them to :mod:`pandas` types.
5. Download the actual data.
      Using :mod:`pandaSDMX`, specify the needed portions of the data from the data flow by constructing a selection ('key') of series and a period/time range.
      Then, retrieve the data using :meth:`Request.get`.
6. Analyze or manipulate the data.
      Convert to :mod:`pandas` types using :meth:`~pandasmdx.message.Message.to_pandas` (or, equivalently, the top level function :func:`~pandasdmx.to_pandas`) 
      and use the result in further Python code.


Choose and connect to an SDMX web service
=========================================

First, we instantiate a :class:`.pandasdmx.Request` object, using the string ID of a :doc:`data source <sources>` supported by :mod:`pandaSDMX`:

.. ipython:: python

    import pandasdmx as sdmx
    ecb = sdmx.Request('ECB')

The object ``ecb`` is now ready to make multiple data and metadata queries to the European Central Bank's web service. 
To send requests to multiple web services, we could instantiate multiple :class:`Requests <.Request>`.

pandaSDMX knows the URLs to the online documentation pages of each data source. 
The  convenience method :meth:`pandasdmx.api.Request.view_doc` opens it in the standard browser.

.. versionadded:: 1.3.0

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

The :attr:`~.Request.session` attribute is a familiar :class:`requests.Session` object that can be used to inspect and modify configuration between queries:

.. ipython:: python

    ecb_via_proxy.session.proxies

For convenience, :attr:`~.Session.timeout` stores the timeout in seconds for HTTP requests, and is passed automatically for all queries.

Cache HTTP responses and parsed objects
---------------------------------------

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


In addition, :class:`.Request` provides an optional, simple dict-based cache for retrieved and parsed :class:`.Message` instances, where the cache key is the constructed query URL.
This cache is disabled by default; to activate it, supply `use_cache=True` to the constructor.

Using custom sessions
--------------------------

.. versionadded:: 1.0.0

The :class:`Request` constructor takes an optional keyword argument `session`.
For instance, a :class:`requests.Session` with pre-mounted adapters 
or patched by  an alternative caching library such as `CacheControl 
<https://pypi.org/project/CacheControl/>`_ 
can  be passed:

    >>> awesome_ecb_req = Request('ECB', session=my_awesome_session)  


Obtain and explore metadata
===========================

This section illustrates how to download and explore metadata.
Suppose we are looking for time-series on exchange rates, and we know that the European Central Bank provides a relevant :term:`data flow`.

.. sidebar:: What is a “data flow”?

   SDMX allows that multiple data providers can publish, at different times, data points about the same measure, with the same dimensions, attributes, etc. For example, two different countries might each publish their own exchange rates with a third country.

   These individual releases are called 'data sets'; the whole collection of similarly-structured data sets is a 'data flow'.

   When using SDMX web services, a request for data from a data flow with a certain ID will yield one or more data sets with observations that match the query parameters.

We *could* search the Internet for the dataflow ID or browse the ECB's website.
However, we can also use :mod:`pandaSDMX` to retrieve metadata and get a complete overview of the dataflows the ECB provides.

Get information about the source's data flows
---------------------------------------------

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

However, an easier way is to use pandasdmx to convert some of the information to a :class:`pandas.Series`:

.. ipython:: python

    dataflows = sdmx.to_pandas(flow_msg.dataflow)
    dataflows.head()
    len(dataflows)

:func:`.to_pandas` accepts most instances and Python collections of :mod:`pandasdmx.model` objects, and we can use keyword arguments to control how each of these is handled.
Under the hood, it calls :func:`pandasdmx.writer.write`. See the function documentation for details. 

If we want to export the entire message content to pandas rather than 
selecting some resource such as dataflows as in the above example, the :meth:`pandasdmx.message.Message.to_pandas` 
comes in handy.
  
As we are interested in exchange rate data, let's use built-in Pandas methods to find an appropriate data flow:

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
    #        exr_msg = ecb.dataflow(resource=flow_msg.dataflow.EXR)
    exr_msg = ecb.dataflow('EXR')
    exr_msg.response.url

    # The response includes several classes of SDMX objects
    exr_msg

    exr_flow = exr_msg.dataflow.EXR

The :attr:`.DataflowDefinition.structure` attribute refers to the data structure definition (DSD, an instance of :class:`.DataStructureDefinition`).
As the name implies, this object contains metadata that describes the structure of data in the 'EXR' flow:

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

Chosing just the ``FREQ`` dimension, we can explore the :class:`.Codelist` that contains valid values for this dimension in the data flow:

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

The ``CURRENCY`` and ``CURRENCY_DENOM`` dimensions of this DSD are both represented using the same ``CL_CURRENCY`` code list.
In order to be reusable for as many data sets as possible, this code list is extensive and complete:

.. ipython:: python

    len(exr_msg.codelist.CL_CURRENCY)

However, the *European* Central Bank does not, in its 'EXR' data flow, commit to providing exchange rates between—for instance—the Congolose franc ('CDF') and Peruvian sol ('PEN').
In other words, the values of (``CURRENCY``, ``CURRENCY_DENOM``) that we can expect to find in 'EXR' is much smaller than the 359 × 359 possible combinations of two values from ``CL_CURRENCY``.

How much smaller?
Let's return to explore the :class:`.ContentConstraint` that came with our metadata query:

.. ipython:: python

    exr_msg.constraint.EXR_CONSTRAINTS

    # Get the content 'region' included in the constraint
    cr = exr_msg.constraint.EXR_CONSTRAINTS.data_content_region[0]

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

We also see that 'USD' and 'JPY' are valid values along both dimensions.

Attribute names and allowed values can be obtained in a similar fashion.


Select and query data from a dataflow
=====================================

Next, we will query some data.
The step is simple: call :meth:`.Request.get` with `resource_type='data'` as the first argument, or the alias :meth:`.Request.data`.

First, however, we describe some of the many options offered by SDMX and :mod:`pandSDMX` for data queries.

Choose a data format
--------------------

Web services offering SDMX-ML–formatted :class:`DataMessages <.DataMessage>` can return them in one of two formats:

Generic data
   use XML elements that explicitly identify whether values associated with an Observation are dimensions, or attributes.

   For example, in the 'EXR' data flow, the XML content for the ``CURRENCY_DENOM`` dimension and for the ``OBS_STATUS`` attribute are stored differently:

   .. code-block:: xml

      <generic:Obs>
        <generic:ObsKey>
          <!-- NB. Other dimensions omitted. -->
          <generic:Value value="EUR" id="CURRENCY_DENOM"/>
          <!-- … -->
        </generic:ObsKey>
        <generic:ObsValue value="0.82363"/>
        <generic:Attributes>
          <!-- NB. Other attributes omitted. -->
          <generic:Value value="A" id="OBS_STATUS"/>
          <!-- … -->
        </generic:Attributes>
      </generic:Obs>

Structure-specific data
   use a more concise format:

   .. code-block:: xml

      <!-- NB. Other dimensions and attributes omitted: -->
      <Obs CURRENCY_DENOM="EUR" OBS_VALUE="0.82363" OBS_STATUS="A" />

   This can result in much smaller messages.
   However, because this format does not distinguish dimensions and attributes, it cannot be properly parsed by :mod:`pandaSDMX` without separately obtaining the data structure definition.

:mod:`pandaSDMX` adds appropriate HTTP headers for retrieving structure-specific data (see :ref:`implementation notes <web-service>`).
In general, to minimize queries and message size:

1. First query for the DSD associated with a data flow.
2. When requesting data, pass the obtained object as the `dsd=` argument to :meth:`.Request.get` or :meth:`.Request.data`.

This allows :mod:`pandaSDMX` to retrieve structure-specific data whenever possible.
It can also avoid an additional request when validating data query keys (below).

Construct a selection `key` for a query
---------------------------------------

SDMX web services can offer access to very large data flows.
Queries for *all* the data in a data flow are not usually necessary, and in some cases servers will refuse to respond.
By selecting a subset of data, performance is increased.

The SDMX REST API offers two ways to narrow a data request:

- specify a **key**, i.e. values for 1 or more dimensions to be matched by returned Observations and SeriesKeys.
  The key is included as part of the URL constructed for the query.
  Using :mod:`pandaSDMX`, a key is specified by the `key=` argument to :mod:`.Request.get`.
- limit the time period, using the HTTP parameters 'startPeriod' and 'endPeriod'.
  Using :mod:`pandaSDMX`, these are specified using the `params=` argument to :mod:`.Request.get`.

From the ECB's dataflow on exchange rates, we specify the ``CURRENCY`` dimension to contain either of the codes 'USD' or 'JPY'.
The documentation for :meth:`.Request.get` describes the multiple forms of the `key` argument and the validation applied.
The following are all equivalent:

.. ipython:: python

    key = dict(CURRENCY=['USD', 'JPY'])
    key = '.USD+JPY...'

We also set a start period to exclude older data:

.. ipython:: python

    params = dict(startPeriod='2016')

Another way to validate a key against valid codes are series-key-only datasets, i.e. a dataset with all possible series keys where no series contains any observation.
pandaSDMX supports this validation method as well.
However, it is disabled by default.
Pass ``series_keys=True`` to the Request method to validate a given key against a series-keys only dataset rather than the DSD.

Query data
----------

Finally, we request the data in generic format:

.. ipython:: python

    import sys

    ecb = sdmx.Request('ECB', backend='memory')
    data_msg = ecb.data('EXR', key=key, params=params)

    # Generic data was returned
    data_msg.response.headers['content-type']

    # Number of bytes in the cached response
    bytes1 = sys.getsizeof(ecb.session.cache.responses.popitem()[1].content)
    bytes1

To demonstrate a query for a structure-specific data set, we pass the DSD obtained in the previous section:

.. ipython:: python

    ss_msg = ecb.data('EXR', key=key, params=params, dsd=dsd)

    # Structure-specific data was requested and returned
    ss_msg.response.request.headers['accept']
    ss_msg.response.headers['content-type']

    # Number of bytes in the cached response
    bytes2 = sys.getsizeof(ecb.session.cache.responses.popitem()[1].content)
    bytes2 / bytes1

The structure-specific message is a fraction of the size of the generic message.

.. ipython:: python

    data = data_msg.data[0]
    type(data)
    len(data.series)
    list(data.series.keys())[5]
    set(series_key.FREQ for series_key in data.series.keys())

This dataset thus comprises 16 time series of several different period lengths.
We could have chosen to request only daily data in the first place by providing the value 'D' for the ``FREQ`` dimension.
In the next section we will show how columns from a dataset can be selected through the information model when writing to a :mod:`pandas` object.

Convert data to pandas
======================

Select columns using the model API
----------------------------------

As we want to write data to a pandas DataFrame rather than an iterator of pandas Series, we avoid mixing up different frequencies as pandas may raise an error when passed data with incompatible frequencies.
Therefore, we single out the series with daily data.
:func:`to_pandas` method accepts an optional iterable to select a subset of the series contained in the dataset.
Thus we can now generate our pandas DataFrame from daily exchange rate data only:

.. ipython:: python

    import pandas as pd
    daily = [s for sk, s in data.series.items() if sk.FREQ == 'D']
    cur_df = pd.concat(sdmx.to_pandas(daily)).unstack()
    cur_df.shape
    cur_df.tail()


.. _datetime:

Convert dimensions to :class:`pandas.DatetimeIndex` or :class:`~pandas.PeriodIndex`
-----------------------------------------------------------------------------------

SDMX datasets often have a :class:`~.Dimension` with a name like ``TIME_PERIOD``.
To ease further processing of time-series data read from pandasdmx messages, :func:`.write_dataset` provides a `datetime` argument to convert these into :class:`pandas.DatetimeIndex` and :class:`~pandas.PeriodIndex` classes.

For multi-dimensional datasets, :func:`~.write_dataset` usually returns a :class:`pandas.Series` with a :class:`~pandas.MultiIndex` that has one level for each dimension.
However, MultiIndex and DatetimeIndex/PeriodIndex are incompatible; it is not possible to use pandas' date/time features for *just one level* of a MultiIndex (e.g. ``TIME_PERIOD``) while using other types for the other levels/dimensions (e.g. strings for ``CURRENCY``).

For this reason, when the `datetime` argument is used, :func:`~.write_dataset` returns a :class:`~pandas.DataFrame`: the DatetimeIndex/PeriodIndex is used along axis 0, and *all other dimensions* are collected in a MultiIndex on axis 1.

An example, using the same data flow as above:

.. ipython:: python

   key = dict(CURRENCY_DENOM='EUR', FREQ='M', EXR_SUFFIX='A')
   params = dict(startPeriod='2019-01', endPeriod='2019-06')
   data = ecb.data('EXR', key=key, params=params).data[0]

Without date-time conversion, :meth:`~.to_pandas` produces a MultiIndex:

.. ipython:: python

   sdmx.to_pandas(data)

With date-time conversion, it produces a DatetimeIndex:

.. ipython:: python

   df1 = sdmx.to_pandas(data, datetime='TIME_PERIOD')
   df1.index
   df1

Use the advanced functionality to specify a dimension for the frequency of a PeriodIndex, and change the orientation so that the PeriodIndex is on the columns:

.. ipython:: python

   df2 = sdmx.to_pandas(
     data,
     datetime=dict(dim='TIME_PERIOD', freq='FREQ', axis=1))
   df2.columns
   df2

.. warning:: For large datasets, parsing datetimes may reduce performance.


Work with files
===============

:meth:`.Request.get` accepts the optional keyword argument `tofile`.
If given, the response from the web service is written to the specified file, *and* the parse :class:`.Message` returned.

.. versionadded:: 0.2.1

A file-like may be passed in a with-context. And OpenFile instances from 
`FSSPEC <https://filesystem-spec.readthedocs.io/en/latest/>`_ may be used, 
e.g., to access a cloud storage provider's file system.

.. versionadded:: 1.2.0

Likewise, :func:`.read_sdmx` can be used 
to load SDMX messages stored in local files or 
remote files using FSSPEC:

.. ipython:: python

    # Use an example ('specimen') file from the pandaSDMX test suite
    from pandasdmx.tests.data import specimen
    # …with time-series exchange rate data from the EU Central Bank
    with specimen('ECB_EXR/ng-ts.xml') as f:
        sdmx.read_sdmx(f)


Handle errors
=============

:attr:`.Message.response` carries the :attr:`requests.Response.status_code` attribute;
in the successful queries above, the status code is ``200``.
The SDMX web services guidelines explain the meaning of other codes.
In addition, if the SDMX server has encountered an error, it may return a Message with a footer containing explanatory notes.
:mod:`pandaSDMX` exposes footer content as :attr:`.Message.footer` and :attr:`.Footer.text`.

.. note::

   :mod:`pandaSDMX` raises only HTTP errors with status code between 400 and 499.
   Codes >= 500 do not raise an error as the SDMX web services guidelines define special meanings to those codes.
   The caller must therefore raise an error if needed.
