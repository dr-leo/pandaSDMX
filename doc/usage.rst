.. _basic-usage:    
    
Basic usage
===============

Overview
----------------------------------

This chapter illustrates the main steps of a typical workflow, namely:

1. retrieving relevant
   dataflows by category or from a complete list of dataflows,  
#. exploring the data structure, related code lists, and other metadata by exporting
   them as pandas DataFrames
#. selecting relevant series (columns) and a time-range (rows) from a dataset provided under the chosen dataflow 
   and requesting data sets via http   
#. exploring the received data using the information model
#. writing a dataset or selected series thereof to a pandas DataFrame or Series 
#. Reading and writing SDMX files
#. odo support
#. Handling errors

These steps share common tasks which flow from the architecture of pandaSDMX:

1. Use a new or existing :class:`pandasdmx.api.Request` instance
   to get an SDMX message from a web service or file 
   and load it into memory. Since version 0.4 this can be conveniently done by descriptors named after the web resources defined by the SDMX standard (``dataflow``, ``categoryscheme``, ``data`` etc.). In older versions, these operations required to call :meth:`pandasdmx.api.Request.get` 
#. Explore the returned :class:`pandasdmx.api.Response` instance 

   * check for errors 
   * explore the SDMX message's content .
   * write data or metadata to a pandas DataFrame or Series by Calling 
     :meth:`pandasdmx.api.Response.write`.      
     
     
Importing pandaSDMX
--------------------------------
    
    As explained in the preceeding section, we will need :class:`pandasdmx.api.Request` all the time.
    Yet, we can use the following shortcut to import it:    
        
.. ipython:: python
        
    from pandasdmx import Request
            
Connecting to an SDMX web service, caching
-----------------------------------------------

We instantiate :class:`pandasdmx.api.Request`. The constructor accepts an optional
agency ID as string. The list of supported agencies
(as of version 0.4: ECB, ESTAT, INSEE) is shown in the error message if an invalid agency ID is passed:
            
.. ipython:: python

    ecb = Request('ECB')
    
``ecb`` is now configured so as to make requests to the European Central Bank. If you want to
send requests to other agencies, you can instantiate multiple ``Request`` objects. 

Configuring the http connection
:::::::::::::::::::::::::::::::::::::

To pre-configure the HTTP connections to be established by a ``Request`` instance, 
you can pass all keyword arguments consumed by the underlying HTTP library 
`requests <http://www.python-requests.org/>`_ (new in version 0.2.2). 
For a complete description of the options see the ``requests``  documentation.
For example, a proxy server can be specified for subsequent requests like so:
   
.. ipython:: python

    ecb_via_proxy = Request('ECB', proxies={'http': 'http://1.2.3.4:5678'})

HTTP request parameters are exposed through a dict. It may be
modified between requests.

.. ipython:: python

    ecb_via_proxy.client.config

The ``Request.client`` attribute acts a bit like a ``requests.Session`` in that it
conveniently stores the configuration for subsequent HTTP requests. Modify it to change the configuration. For convenience, :class:`pandasdmx.api.Request` has
a ``timeout`` property to set the timeout in seconds for http requests.    

Caching received files
::::::::::::::::::::::::::

Since version 0.3.0, `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ is supported. To use it, 
pass an optional ``cache`` keyword argument to ``Request()`` constructor.
If given, it must be a dict whose items will be passed to ``requests_cache.install_cache`` function. Use it if you
want to cache SDMX messages in databases such as MongoDB, Redis or SQLite. 
See the `requests-cache`` docs for further information.
     
Loading a file instead of requesting it via http
::::::::::::::::::::::::::::::::::::::::::::::::::::

Any ``Request`` instance
can load SDMX messages from local files. 
Issuing ``r = Request()`` without passing any agency ID
instantiates a ``Request`` object not tied to any agency. It may only be used to
load SDMX messages from files, unless a pre-fabricated URL is passed to :meth:`pandasdmx.api.Request.get`.

Obtaining and exploring metadata about datasets
------------------------------------------------

This section illustrates by a typical use case how to download and explore metadata.
Assume we are looking for time-series on exchange rates. Our best guess is
that the European Central Bank provides a relevant dataflow. We could
google for the dataflow ID or browse through the ECB's website. However,
we choose to use SDMX metadata, namely category-schemes to get a complete overview of
the dataflows the ECB provides. 

.. note::
    Some data providers such as the ECB and INSEE,
    but not Eurostat,
    support category-schemes to
    facilitate dataflow retrieval. If you already know, e.g., from
    the data provider's website or other publications, what
    dataflows you are looking for, you won't need this step.
    Yet this section should still be useful as
    it demonstrates how metadata can be explored
    using pandas DataFrames.
    
               
Getting the category scheme
:::::::::::::::::::::::::::::::::::::::

SDMX allows to download a list of dataflow definitions for all
dataflows provided by a given data provider. As these lists may be very long,
SDMX supports category-schemes to categorize dataflow definitions and other objects. Note that
the terms 'dataflow' and 'dataflow definition' are used synonymously.

To search the list of dataflows by category, we request the category scheme from the 
ECB's SDMX service and explore the response like so:

.. ipython:: python

    cat_response = ecb.categoryscheme()
    
The content of the SDMX message, its header and its payload are exposed as attributes. These are also accessible directly from the containing
:class:`pandasdmx.api.Response` instance (new in version 0.4). We will use this
shortcut throughout this documentation. But keep in mind
that all payload such as data or metadata 
is stored as attributes of a 
:class:`pandasdmx.model.Message` instance which can be
explicitly accessed from a ``Response`` instance via its ``msg`` attribute.
  
Try ``dir(cat_response.msg)`` to see what we have received: 
There is not only the category scheme, but also the dataflows and categorisations.
This is because the ``get`` method has conveniently set the ``references`` parameter
to a default value. We can see this from the URL:

.. ipython:: python

    cat_response.url

The HTTP headers returned by the SDMX server are availble as well (new in version 0.2.2):

.. ipython:: python

    cat_response.http_headers
    
Now let's export our
category scheme to a pandas DataFrame and see what's in there:  

.. ipython:: python

    cat_response.write().categoryscheme

The :meth:`pandasdmx.api.Response.write` returns a mapping
from the metadata contained in the :class:`pandasdmx.model.StructureMessage` instance to pandas DataFrames.
E.g., there is a key and corresponding DataFrame for the resource ``categoryscheme``. The mapping object is a thin wrapper around :class:`dict`
which essentially enables attribute syntax for read access.   

The ``write``-method accepts a number of
keyword arguments to choose the resources to be exported, the attributes to be included
in the DataFrame columns, and the desired language. See the doc string for
details.

There are three category-schemes.
As we are interested in exchange rate data, we will have a closer look
at category '07' of category-scheme 'MOBILE_NAVI'.  

Extracting the dataflows in a particular category
::::::::::::::::::::::::::::::::::::::::::::::::::

To display the categorised items, in our case the dataflow definitions contained in the category
on exchange rates, we iterate over the `Category` instance (new in version 0.5): 
 
.. ipython:: python

    list(cat_response.categoryscheme.MOBILE_NAVI['07'])


Retrieving dataflows without using categories
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

In the previous section we have used categories to find relevant dataflows. However,
in many situations there are no categories to narrow down the result set.
We can export the dataflow definitions to a 
pandas DataFrame and use pandas' text search capabilities to find dataflows of interest:

.. ipython:: python

    cat_response.write().dataflow.head()
 
Moreover, the old :meth:`pandasdmx.utils.DictLike.find` is still available.
    
Extracting the data structure and data from a dataflow
-----------------------------------------------------------

In this section we will focus on a particular dataflow. We will use the 'EXR' dataflow from the
European Central Bank. In the previous section we already obtained the dataflow definitions by requesting 
the categoryschemes with the appropriate references. But this works only if the SDMX services supports 
category schemes. If not (and many agencies don't), we need to download the dataflow definitions
explicitly by issuing:

    >>> flows = ecb.dataflow()

Dataflow definitions at a glance
:::::::::::::::::::::::::::::::::::

A :class:`pandasdmx.model.DataFlowDefinition` has an ``id`` , ``name`` , ``version``  and many
other attributes inherited from various base classes. It is worthwhile to look at the method resolution order to see
how it works. Many other classes from the model have similar base classes. 

It is crucial to bear in mind two things:
 
* the ``id``  of a dataflow definition is also used to request data of this dataflow.
* the ``structure``  attribute of the dataflow definition.
  is a reference to the data structure definition describing datasets of this dataflow.
  
  
Getting the data structure definition (DSD)
::::::::::::::::::::::::::::::::::::::::::::::

We can extract the DSD's ID from the dataflow definition 
and download the DSD together with all artefacts
that it refers to and that refer to it. We set the ``params`` keyword argument 
explicitly to the default value to show how it works.

.. ipython:: python

    dsd_id = cat_response.dataflow.EXR.structure.id
    dsd_id
    refs = dict(references = 'all')
    dsd_response = ecb.datastructure(resource_id = dsd_id, params = refs)
    dsd = dsd_response.datastructure[dsd_id]
 
A DSD essentially defines three things:

* the dimensions of the datasets of this dataflow,
  i.e. the order and names of the dimensions and the allowed
  values or the data type for each dimension, and
* the attributes, i.e. their names, allowed values and where each may be
  attached. There are four possible attachment points:
  
  - at the individual observation
  - at series level
  - at group level (i.e. a subset of series defined by dimension values)
  - at dataset level.   

* the measures

Let's look at the dimensions and for the 'CURRENCY' dimension 
also at the allowed values
as enumerated in the referenced code list:

.. ipython:: python

    dsd.dimensions.aslist()
    dsd_response.write().codelist.loc['CURRENCY'].head()    
    
The order of dimensions will determine the order of column index levels of the
pandas DataFrame (see below).

The DataFrame representation of the code list for the
CURRENCY dimension shows that 'USD' and 'JPY' are valid dimension values. 
We need this information to construct a filter
for our dataset query which should be limited to
the currencies we are interested in.

Note that :meth:`pandasdmx.model.Scheme.aslist` sorts the dimension objects by their position attribute. 
The order matters when constructing filters for dataset queries (see below). But pandaSDMX sorts filter values behind the scenes, so we need not care. 

Attribute names and allowed values can be obtained 
in a similar fashion. 

.. note::

    Groups are not yet implemented in the DSD. But this is not a problem    
    as they are implemented for generic datasets. Thus, datasets should be rendered properly including all attributes and their 
    attachment levels.
    
Working with datasets
------------------------------

Selecting and requesting data from a dataflow
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

Requesting a dataset is as easy as requesting a dataflow definition or any other
SDMX artefact: Just call the :meth:`pandasdmx.api.Request.get` method and pass it 'data' as the resource_type and the dataflow ID as resource_id. Alternatively, you can use the
``data`` descriptor which calls the ``get`` method implicitly.  

However, we only want to download those parts of the data we are 
interested in. Not only does this increase
performance. Rather, some dataflows are really huge, and would exceed the server or client limits.
The REST API of SDMX offers two ways to narrow down a data request:
 
* specifying dimension values which the series to be returned must match ("horizontal filter") or
* limiting the time range or number of observations per series ("vertical filter") 
  
From the ECB's dataflow on exchange rates, 
we specify the CURRENCY dimension to be either 'USD' or 'JPY'.
This can be done by passing a ``key``  keyword argument to the ``get``  method or the ``data`` descriptor. 
It may either be a string (low-level API) or a dict. The dict form 
introduced in v0.3.0 is more convenient and pythonic
as it allows pandaSDMX to infer the string form from the dict. 
Its keys (= dimension names) and
values (= dimension values) will be validated against the 
datastructure definition as well as the content-constraint if available. 

Content-constraints are
implemented only in their CubeRegion flavor. KeyValueSets are not yet supported. In this
case, the provided demension values will be validated only against the code-list. It is thus not
always guaranteed that the dataset actually contains the desired data, e.g., 
because the country of
interest does not deliver the data to the SDMX data provider.  
 
If we choose the string form of the key, 
it must consist of
'.'-separated slots representing the dimensions. Values are optional. As we saw
in the previous section, the ECB's dataflow for exchange rates has five relevant dimensions, the
'CURRENCY' dimension being at position two. This yields the key '.USD+JPY...'. The '+' can be
read as an 'OR' operator. The dict form is shown below.

Further, we will set the start period for the time series to 2014 to
exclude any prior data from the request.

.. ipython:: python

    data_response = ecb.data(resource_id = 'EXR', key={'CURRENCY': 'USD+JPY'}, params = {'startPeriod': '2016'})
    data = data_response.data
    type(data)
    
Datasets 
::::::::::::::::::::

This section explains the key elements and structure of data sets. You can skip
it on first read when you just want to be able to download data and
export it to pandas. More advanced operations, e.g., exporting only a subset of series to pandas, requires some understanding of
the anatomy of a data set including observations and attributes. 

As we saw in the previous section,
the datastructure definition (DSD) is crucial to understanding the data structure, the meaning of dimension
and attribute values, and to select series of interest from the entire data set
by specifying a valid key.

The :class:`pandasdmx.model.DataSet` class has the following features:

``dim_at_obs``  
    attribute showing which dimension is at
    observation level. For time series its value is either 'TIME' or 'TIME_PERIOD'. If it is
    'AllDimensions', the dataset is said to be flat. In this case there are no series, just a
    flat list of observations.
series
    property returning an iterator over :class:`pandasdmx.model.Series` instances
obs
    method returning an iterator over the observations. Only for flat datasets.
attributes
    namedtuple of attributes, if any, that are
    attached at dataset level
       
The :class:`pandasdmx.model.Series` class has the following features:

key
    nnamedtuple mapping dimension names to dimension values
obs
    method returning an iterator over observations within the series
attributes:
    namedtuple mapping any attribute names to values
groups
    list of :class:`pandasdmx.model.Group` instances to which this series belongs.
    Note that groups are merely attachment points for attributes.
        
.. ipython:: python

    data.dim_at_obs
    series_l = list(data.series)
    len(series_l)
    series_l[5].key
    set(s.key.FREQ for s in data.series)
    

This dataset thus comprises 16 time series of several different period lengths.
We could have chosen to request only daily data 
in the first place by providing the value ``D`` for the ``FREQ`` dimension. In the next section
we will show how columns from a dataset can be selected through the 
information model when writing to a pandas DataFrame.

Writing to pandas
::::::::::::::::::::::

Selecting columns using the model API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As we want to write data to a pandas DataFrame rather than an iterator of pandas Series, 
we must not mix up the time spans. 
Therefore, we
single out the daily data first.  
The :meth:`pandasdmx.api.Response.write` method accepts an optional iterable to select a subset
of the series contained in the dataset. Thus we can now
generate our pandas DataFrame from daily exchange rate data only:

.. ipython:: python

    daily = (s for s in data.series if s.key.FREQ == 'D')
    cur_df = data_response.write(daily)
    cur_df.shape
    cur_df.tail()

Controlling the output
~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
The docstring of the :meth:`pandasdmx.writer.data2pandas.Writer.write` method explains
a number of optional arguments to control whether or not another dataframe should be generated for the
attributes, which attributes it should contain, and, most importantly, if the resulting
pandas Series should be concatenated to a single DataFrame at all (``asframe = True`` is the default).

Controlling index generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``write``  method provides the following parameters to control index generation. 
This is useful to increase performance for
large datasets with regular indexes (e.g. monthly data, and to avoid crashes caused
by exotic datetime formats not parsed by pandas:

* ``fromfreq``: if True, the index will be extrapolated from the first date or period and the frequency. 
  This is only robust if the dataset has a uniform index, 
  e.g. has no gaps like for daily trading data.
* ``reverse_obs``:: if True, return observations in a series in reverse 
  document order. This may be useful to establish chronological order, 
  in particular incombination with ``fromfreq``. Default is False.  
* If pandas raises parsing errors due to exotic date-time formats, 
  set ``parse_time`` to False to obtain a string index 
  rather than datetime index. Default is True. 

Working with files
---------------------

The :meth:`pandasdmx.api.Request.get` method accepts two optional keyword
arguments ``tofile``  and ``fromfile``. If a file path or, in case of ``fromfile``, 
a  file-like object is given,
any SDMX message received from the server will be written to a file, or a file will be read
instead of making a request to a remote server. 

The file to be read may be a zip file (new in version 0.2.1). In this case, the SDMX message
must be the first file in the archive. The same works for
zip files returned from an SDMX server. This happens, e.g., when
Eurostat finds that the requested dataset has been too
large. In this case the first request will yield
a message with a footer containing a link to a zip file to be made
available after some time. The link may be extracted by issuing something like:
 
    >>> resp.footer.text[1]  
    
and passed as ``url`` argument when calling ``get`` a second time to
get the zipped data message. 

Since version 0.2.1, this second request can be performed automatically through the
``get_footer_url`` parameter. It defaults to ``(30, 3)`` which means that three attempts will be made in 30 seconds intervals. 
This behavior is useful when requesting large datasets from Eurostat. Deactivate it by setting ``get_footer_url`` to None.   

In addition, since version 0.4 you can use :meth:`pandasdmx.api.Response.write_source` to save the
serialized XML tree to a file.    

Caching Response instances in memory
-----------------------------------------------

The ''get'' API provides a rudimentary cache for Response instances. It is a
simple dict mapping user-provided names to the Response instances.
If we want to cache a Response, we can provide a suitable name by passing the keyword argument ``memcache`` to the get method. 
Pre-existing items under the same key will
be overwritten. 

.. note::
    Caching of http responses can also be achieved through ''requests-cache'. 
    Activate the cache by instantiating :class:`pandasdmx.api.Request` passing a keyword
    argument ``cache``. It must be a dict mapping config and other values.      

Using odo to export data sets to other data formats and database backends
---------------------------------------------------------------------------

Since version 0.4, pandaSDMX supports `odo <http://odo.readthedocs.io>`_, a great tool to convert data sets
to a variety of data formats and database backends. To use this feature, you have to
call :func:`pandasdmx.odo_register` to register .sdmx files with odo. Then you can
convert an .sdmx file containing a data set to, say, a CSV file or an SQLite or PostgreSQL database in
a few lines::

    >>> import pandasdmx
    >>> from odo import odo
    ___ pandasdmx.odo_register()
    >>> odo('mydata.sdmx', 'sqlite:///mydata.sqlite')
    
Behind the scenes, odo uses pandaSDMX to convert the .sdmx file
to a pandas DataFrame and performs any further conversions from there based on odo's
conversion graph. Any keyword arguments passed to odo will
be passed on to :meth:`pandasdmx.api.Response.write`.

There is a limitation though: In the exchange rate example from the previous chapter, we
needed to select same-frequency series from the data set before converting the
data set to pandas. This will likely cause crashes as odo's discover method is unaware of this selection. Hence, .sdmx files can only be exported using odo if they
can be exported to pandas without passing any arguments to :meth:`pandasdmx.api.Response.write`.
      
Handling errors
----------------

The :class:`pandasdmx.api.Response` instance generated upon receipt of the response from the server 
has a ``status_code``  attribute. The SDMX web services guidelines explain the meaning
of these codes. In addition,
if the SDMX server has encountered an error, 
it may return a message which
includes a footer containing explanatory notes. pandaSDMX exposes the content of
a footer via a ``text`` attribute which is a list of strings.

.. note::
    pandaSDMX raises only http errors with status code between 400 and 499.
    Codes >= 500 do not raise an error as the SDMX web services guidelines
    define special meanings to those codes. The caller must therefore raise an error if needed. 
       
Logging
-----------

Since version 0.4, pandaSDMX can log certain events such as when a connection 
to a web service is made or a file has been successfully downloaded. It uses the logging package from the Python stdlib. . To activate logging, you must
set the parent logger's level to the desired value as described in the logging docs. Example::
       
    >>> pandasdmx.logger.setLevel(10)
                     
       