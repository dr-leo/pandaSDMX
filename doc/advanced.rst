Advanced topics
===================



Debugging the information model
--------------------------------------

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

  