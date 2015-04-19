:tocdepth: 1

What's new?
==============

v0.2.1
--------------

* Request.get: allow `fromfile` to be a file-like object
* extract SDMX messages from zip file if given. Important for large datasets from Eurostat
* automatically get a resource at an URL given in
  the footer of the received message. This allows to automatically get large datasets from Eurostat that have been
  made available at the given URL. The number of attempts and the time to wait before each
  request are configurable via the ``get_footer_url`` argument. 
 

v0.2 (2015-04-13)
-----------------------

This version is a quantum leap. The whole project has been redesigned and rewritten from
scratch to provide robust support for many SDMX features. The new architecture is centered around
a pythonic representation of the SDMX information model. It is extensible through readers and writers
for alternative input and output formats. 
Export to pandas has been dramatically improved. Sphinx documentation
has been added.

v0.1 (2014-09)
----------------

Initial release

 

