Advanced topics
===================



References in the SDMX information model and REST APIs
---------------------------------------------------------

Background
:::::::::::::

Some SDMX artefacts (objects) reference others to indicate a relationship between
both objects. pandaSDMX represents such references as instances of :class:`pandasdmx.model.Ref`.  

Examples:

* the ``structure`` attribute of :class:`pandasdmx.model.DataflowDefinition`
* the ``enum`` attribute of :class:`Representation` attached as ``local_repr`` attribute
  of a :class:`pandasdmx.model.Dimension` object within a DSD.
* the ``attached_to`` attribute of a :class:`ContentConstraint` 
   
 Such references can be considered as edges of a directed graph whose nodes are the SDMX objects.
 Objects referenced by another are denoted as its children. These and their children are called its
 descendents. Objects referring to anoter object are called its parents and so forth. Siblings of an object are on the same level of the graph considered
 as multi-rooted tree.   
 
For example, the DSD referenced by a DataflowDefinition is its child, the codelist referenced
by the dimensions defined in the DSD are children of that child, 
i.e. descendants of said DataflowDefinition.

The :class:`pandasdmx.model.Ref`
:::::::::::::::::::::::::::::::::::::::::::::::::::

:class:`pandasdmx.model.Ref` instances identify the referenced target by attributes such as id, agency_id,
package (= resource type) etc. To resolve a reference, i.e. to retrieve the target, Ref instances are
callable (new in v0.9). The __call__ method accepts some arguments to influence the
retrieval process. 

* Set ``request`` to True to allow
  remote requests in case the target is not found in the current message. 
* Set ``target_only`` to False
  if you want the entire SDMX message that has been downloaded rather than just the referenced artefact. 
* ``raise_errors`` specifies whether an exception will be raised or suppressed (in which case
  None is returned.

Using references in requests 
:::::::::::::::::::::::::::::::::::::::

SDMX web services support a ``references`` parameter in HTTP requests which can take on values such as 'all', 
'descendants' and so forth. This parameter instructs the web service to include, when generating the
DataMessage of StructureMessage, the objects implicitly designated by the ``references`` parameter alongside the  
explicit resource. For example, in the request
 
 >>> response = some_agency.dataflow('SOME_ID', params={'references': 'all'})

the agency will return

* the dataflow 'SOME_ID' explicitly specified 
* the DSD referenced by the dataflow's ``structure`` attribute
* the codelists referenced indirectly by the DSD
* any content-constraints which reference the dataflow or the DSD.

It is much more efficient to request many objects in a single request. Thus, pandaSDMX
provides sensible defaults for the ``references`` parameter in common situations. For example, when
a single dataflow is requested by specifying its ID, pandaSDMX sets ``references`` to 'all' as this appears
most useful. On the other hand, when the dataflow ID is wildcarded, it is more practical not to
request all referenced objects alongside as the response would likely be excessively large, and the user is deemed to be interested in
the bird's eye perspective (list of dataflows) prior to focusing on a particular dataflow and its descendents and ancestors. The default value for the
``references`` parameter can be overridden.

Note that some agencies differ in their behavior regarding the references parameter.
E.g., Eurostat (ESTAT) does not return the DSD when requesting
a dataflow even though ``references`` is set to 'all'. This behavior is likely inconsistent with the
SDMX standard. 


Category schemes
--------------------

SDMX supports category-schemes to categorize dataflow definitions and other objects. 
This helps retrieve, e.g., a dataflow of interest. Note that not all agencies support
categoryschemes. A good example is the ECB. However, as the ECB's SDMX service offers less than 100 dataflows, using categoryschemes is not strictly
necessary. A counter-example is Eurostat which offers more
than 6000 dataflows, yet does not categorize them. Hence,
the user must search through the flat list of dataflows.

To search the list of dataflows by category, we request the category scheme from the 
ECB's SDMX service and explore the response like so:

.. ipython:: python

    from pandasdmx import *
    ecb = Request('ecb')
    cat_response = ecb.categoryscheme()

Like any other scheme, a category scheme is essentially a dict mapping ID's 
to the actual SDMX objects.
To display the categorised items, in our case the dataflow definitions contained in the category
on exchange rates, we iterate over the `Category` instance (new in version 0.5): 
 
.. ipython:: python

    cat_response.categoryscheme.keys()
    list(cat_response.categoryscheme.MOBILE_NAVI['07'])

    
The information model in detail
------------------------------------------------------------

The easiest way to understanding the class hierarchy of the information model is to download a
DSD from a data provider and inspect the resulting objects' base classes and MRO.

In most situations, structure metadata is represented by subclasses of :class:`dict` mapping the SDMX artifacts' ID's
to the artefacts themselves. The most intuitive examples are the container of code lists and the codes within
a code list.

Likewise, categorisations, categoryschemes, and many other 
artefacts from the SDMX information model are represented by
subclasses of ``dict``.     
    
If dict keys are valid attribute names, you can use attribute syntax. This is thanks to
:class:`pandasdmx.utils.DictLike`, a thin wrapper around ``dict`` that internally uses a patched third-party tool.

In particular, the ``categoryscheme`` attribute of a 
:class:`pandasdmx.model.StructureMessage`instance is an instance of ``DictLike``. The ``DictLike `` 
container for the received category schemes uses the ``ID`` attribute of :class:`pandasdmx.model.CategoryScheme` as keys.
This level of generality is required to cater for situations in which more than one category scheme is 
returned. 

Note that 
:class:`pandasdmx.model.DictLike` has a `` aslist``  method. It returns its values as a new
list sorted by ``id``. The sorting criterion may be overridden in subclasses. We can see this
when dealing with dimensions in a :class:`pandasdmx.model.DataStructureDefinition` where the dimensions are
ordered by position. 

Accessing the underlying XML document
------------------------------------------

The information model does not (yet) expose all attributes of SDMX messages. However, the underlying XML elements are 
accessible from almost everywhere. This is thanks to the base class :class:`pandasdmx.model.SDMXObject`.
It injects two attributes: ``_elem``  and ``_reader``  which
grant access to the XML element represented by the model class instance as well as the reader instance.

Extending pandaSDMX
---------------------

pandaSDMX is now extensible by readers and writers. While the API needs a few refinements, it should be straightforward to
depart from :mod:`pandasdmx.writer.data2pandas` to develop writers for alternative output formats such as 
spreadsheet, database, or web applications. 

Similarly, a reader for the upcoming JSON-based SDMX format would be useful.

Interested developers should contact the author at fhaxbox66@gmail.com.

  