Advanced topics
===================


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

  