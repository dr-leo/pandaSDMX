.. _basic-usage:    
    
Basic usage
===============

Overview, general principles
----------------------------------

This chapter illustrates the main steps of a typical workflow, namely:

1. retrieving relevant
   dataflows by category or from a complete list of dataflows,  
#. exploring the data structure definition of the selected dataflow
#. obtaining a dataset
#. writing a dataset to a pandas DataFrame or Series 
#. Exploring a dataset through the information model
#. Handling errors

All these steps share some principles which flow from the architecture of pandaSDMX:

1. Call :meth:`get` on a new or existing :class:`pandasdmx.api.Request` instance
   to obtain an SDMX message from a web service or a file and load it into memory
#. Explore the :class:`pandasdmx.api.Response`instance returned by :meth:`pandasdmx.Request.get`

   * Access the SDMX message's content through its ``msg``  attribute.
   * Call :meth:`pandasdmx.api.Response.write` to execute the writer. This
     works only for generic data messages.       
     
     
Importing pandaSDMX
--------------------------------
    
    As explained in the preceeding section, we will need :class:`pandasdmx.api.Request` all the time.
    Yet, we can use the following shortcut to import it:    
        
.. ipython:: python
        
    from pandasdmx import Request
            
Selecting an SDMX web service
--------------------------------------

Next, we instantiate :class:`pandasdmx.api.Request`. The constructor accepts an optional
agency ID as string. The list of supported agencies
is shown isplayed in the error message if an invalid agency ID is passed:
            
.. ipython:: python

    Request('foo')
    ecb = Request('ECB')
    
``ecb`` is now configured so as to make requests to the European Central Bank. If you want to
send requests to other agencies, simply instantiate dedicated ``Request`` objects. Note that any ``Request`` instance
can load SDMX messages from local files. Issuing ``r = Request()`` without passing any agency ID will
instantiate a ``Request`` object not tied to any agency. It may only be used to
load SDMX messages from files.

Finding dataflows
-------------------

Getting the categorisation scheme
:::::::::::::::::::::::::::::::::::::::

We can search the list of dataflows offered by a given SDMX web service by
category:. To do this, we request the category scheme from the 
ECB's SDMX service and explore the response like so:

.. ipython:: python

    cat_resp = ecb.get(resource_type = 'categoryscheme')
    type(cat_resp)
    cat_msg = cat_resp.msg
    type(cat_msg)
    cat_header = cat_msg.header
    type(cat_header)
    categorisations = cat_msg.categorisations
    type(categorisations)
   
    
The content of the SDMX message, its header and its payload are exposed as attributes. Try ``dir(cat_msg)`` to find out
that we have not only obtained the category scheme, but also the dataflows and categorisations.
This is because the ``get`` method has set the ``references`` parameter
to the appropriate default value. We can see this from the URL:

.. ipython:: python

    cat_resp.url
    
Note that categorisations, categoryschemes, and many other 
artefacts from the SDMX information model are represented by
subclasses of ``dict``.     
    
.. ipython:: python

    categorisations.__class__.__mro__
    
If dict keys are valid attribute names, you can use attribute syntax. This is thanks to
:class:`pandasdmx.utils.DictLike`, a thin wrapper around ``dict`` that internally uses a slightly patched third party tool.

In the same vein, ``categoryschemes`` is an instance of ``DictLike``. This is
because by calling `` ecb.get``  without specifying a resource_id,
we instructed the SCMX service to return all available categorisation schemes. The ``DictLike`` 
container for the received category schemes uses the ``ID`` attribute of :class:`pandasdmx.model.CategoryScheme` as keys.
This level of generality is required to cater for situations in which more than one category scheme is 
returned. In our example, however, there is but one:

.. ipython:: python

    cs = cat_msg.categoryschemes
    type(cs)
    list(cs.keys())
    
:class:`pandasdmx.model.CategoryScheme` inherits from :class:`pandasdmx.utils.DictLike` as well. Its values are 
:class:`pandasdmx.model.Category` instances, its keyse are their `` id``  attributes. Note that 
:class:`pandasdmx.model.DictLike` has a `` aslist``  method. It returns its values as a new
list sorted by `` id``. The sorting criterion may be overridden in subclasses. We shall see this
when dealing with dimensions in a :class:`pandasdmx.model.DataStructureDefinition` where the dimensions are
ordered by position. 

We can explore our
category scheme like so:  

.. ipython:: python

    cs0 = cs.aslist()[0]
    type(cs0)

    # Print the number of categories    
    len(cs0)
    # Print ID's of categories 
    list(cs0.keys())
    # English name of this category 
    cs0['07'].name.en 
    
Extracting the dataflows in a particular category
::::::::::::::::::::::::::::::::::::::::::::::::::

As we saw from the attributes of ``cat_msg``, the SDMX message, we have
already the categorisations at hand. While in the SDMXML file categories are represented as a
flat list, pandaSDMX groups them by category and exposes them as a :class:`pandasdmx.utils.DictLike`mapping
each category ID to a list of :class:`pandasdmx.model.Categorisation` instances each of which
links its category to a :class:`pandasdmx.model.DataFlowDefinition` instance. Technically, these links
are represented by :class:`pandasdmx.model.Reference` instances whose `` id`` attribute enables us to access the
dataflow definitions in the selected category '07'. We can print the 
string representations of the
dataflows in this categories:

 
.. ipython:: python

    cat07_l = cat_msg.categorisations['07']
    list(cat_msg.dataflows[i.artefact.id] for i in cat07_l)
     
These are all dataflows offered by the ECB in the category on exchange rates. 

Search for items by attribute
:::::::::::::::::::::::::::::::::::::

In the previous section we have used categories to find relevant dataflows. However,
in many situations there are no categories to narrow down the result set. 
Here, :meth:`pandasdmx.utils.DictLike.find` comes in handy:


.. ipython:: python

    cat_msg.dataflows.find('rates')
    
Extracting the data structure and data from a dataflow
-----------------------------------------------------------

In this section we will focus on a particular dataflow. We will use the 'EXR' dataflow from the
European Central Bank. In the previous section we already obtained the dataflow definitions by requesting 
the categoryschemes with the appropriate references. But this works only if the SDMX services supports 
category schemes. If not (and many agencies don't), we need to download the dataflow definitions
explicitly by issuing:

    >>> flows = ecb.get(resource_type = 'dataflow')

Dataflow definitions at a glance
:::::::::::::::::::::::::::::::::::

A :class:`pandasdmx.model.DataFlowDefinition` has an `` id`` , ``name`` , ``version``  and many
other attributes inherited from various base classes. It is worthwhile to look at the method resolution order to see
how it works. Many other classes from the model have similar base classes. 

It is crucial to bear in mind two things:
 
* the `` id``  of a dataflow definition is also used to request data of this dataflow.
* the ``structure``  attribute of the dataflow definition.
  is a reference to the data structure definition describing datasets of this dataflow.
  
  
Getting the data structure definition (DSD)
::::::::::::::::::::::::::::::::::::::::::::::

We can extract the DSD's ID and request the DSD. Then we will 
show some of its attributes.

Next, we extract the DSD's ID and download the DSD together with all artefacts
that it refers to and that refer to it. We set the ``params`` keyword argument 
explicitly to show how it works.

.. ipython:: python

    dsd_id = cat_msg.dataflows.EXR.structure.id
    dsd_id
    refs = dict(references = 'all')
    dsd_resp = ecb.get(resource_type = 'datastructure', resource_id = dsd_id, params = refs)
    dsd = dsd_resp.msg.datastructures[dsd_id]
 
A DSD essentially defines two things:

* the dimensions of the datasets of this dataflow,
  i.e. the order and names of the dimensions and the permissible
  values or the data type for each dimension, and
* the attributes, i.e. their names, permissible values and where each may be
  attached. There are four possible attachment points:
  
  - at the individual observation
  - at series level
  - at group level (i.e. a subset of series defind by dimension values)
  - at dataset level.   

Let's look at the dimensions and for one at the allowed values
as enumerated in the referenced codelist:

 
.. ipython:: python

    list(d.id for d in dsd.dimensions.aslist())
    currency_codelist = dsd.dimensions.CURRENCY.local_repr.enum
    len(currency_codelist)
    'USD' in currency_codelist
    

So there are five dimensions. The 'CURRENCY' dimension stands at position 2.
We want to find out what dimension values are allowed as we need this information to construct a filter
for our dataset query which should be limited to
the currencies we are interested in.

Note that :meth:`pandasdmx.model.Scheme.aslist` sorts the dimension objects by their position attribute. 
The order matters when constructing filters for dataset queries (see below). 

Attribute names and allowed values can be obtained 
in a similar fashion. 

.. note::

    Groups are not yet implemented in the DSD. But this is not a big problem    
    as they are implemented for generic datasets. Thus, datasets should be rendered properly including all attributes and their 
    attachment levels.

    
Working with datasets
------------------------------

Narrowing down the result
::::::::::::::::::::::::::::::::::::::::::

Requesting a dataset is as easy as requesting a dataflow definition or any other
SDMX artefact: Just call the :meth:`pandasdmx.api.Request.get` method and pass it 'data' as the resource_type and the dataflow ID as resource_id.  

However, we only want to download those parts of the data we are 
interested in. Not only does this increase
efficiency. Rather, some dataflows are really huge, and would exceed the server limits.
The REST API of SDMX offers to ways to narrow down a data request:
 
* specifying dimension values which the series to be returned must match ("horizontal filter") or
* limiting the time range or number of observations per series ("vertical filter") 
  
Here we will specify the CURRENCY dimension to be either 'USD' or 'JPY'.
This can be done by passing a ``key``  keyword argument to the ``get``  method. It consists of
'.'-separated slots representing the dimensions. Values are optional. As we saw
in the previous section, the ECB's dataflow for exchange rates has five dimensions, the
'CURRENCY' dimension being at position two. This yields the key '.USD+JPY...'. The '+' can be
read as an 'OR' operator. 

.. ipython:: python

    data_resp = ecb.get(resource_type = 'data', resource_id = 'EXR', key = '.USD+JPY...')
    type(data_resp.msg)
    data = data_resp.msg.data
    type(data)
    
Generic datasets 
::::::::::::::::::::

As per v0.2, pandaSDMX can only process generic datasets, i.e. datasets that encompass sufficient
structural information to be interpreted without consulting the related DSD. However, as we saw,
we need the DSD anyway to understand the data structure, the meaning of dimension
and attribute values, and to construct 
the horizontal filter.

The :class:`pandasdmx.model.GenericDataSet` has the following features:

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
       
The :class:`pandasdmx.model.Series` has the following features:

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
    daily = (s for s in data.series if s.key.FREQ == 'D')

We see that this dataset comprises 16 time series of four different period lengths: annual, semestrial, quarterly, and daily.
As we want to write some data to a pandas DataFrame, we must not mix up the time spans. We decided to 
single out daily data.  


Writing to pandas
::::::::::::::::::::::

The :meth:`pandasdmx.api.Response.write` accepts an optional iterable to select a subset
of the series contained in the dataset. Thus we can now
generate our pandas DataFrame:

.. ipython:: python

    cur_df = data_resp.write(daily)
    cur_df.shape
    cur_df.tail()
    
The docstring of :meth:`pandasdmx.writer.data2pandas.Writer.write` explains
a number of optional arguments to control whether or not another dataframe should be generated for the
attributes, which attributes it should contain, and, most importantly, if the resulting
pandas Series should be concatenated to a single DataFrame at all.

Working with files
---------------------

The :class:`pandasdmx.api.Request.get` method accepts two optional keyword
arguments ``tofile``  and ``fromfile``. If specified,
any SDMX message received from the server will be written to a file, or a file will be read
instead of making a request to a remote server.

Handling errors
----------------

The :class:`pandasdmx.api.Response` instance generated after the response from the server has
been received has a ``status_code``  attribute. The SDMX web services guidelines explain the meaing
of these codes. In addition,
if the SDMX server has encountered an error, 
it may return a message which
includes a footer containing explanatory notes. For instance, if Eurostat cannot 
return a large dataset immediately, it may make it available after some time under a link
contained in the footer. This link should then passed to the `` get`` method using the `` url``  keyword parameter.


    