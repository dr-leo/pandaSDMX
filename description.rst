=============
pandaSDMX
=============




pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ 
package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <http://www.sdmx.org>`_ format. 
It should work with all
SDMX data providers supporting SDMX 2.1. Currently,
this is tested for the European statistics office (Eurostat),
and the European Central Bank (ECB) each providing hundreds of
thousands of indicators. 

While pandaSDMX is extensible to 
cater any output format, it currently supports only `pandas <http://pandas.pydata.org>`_, the gold-standard 
of data analysis in Python. But from pandas you can export your data to Excel and friends. 

Main features
---------------------

* intuitive API inspired by `requests <https://pypi.python.org/pypi/requests/>`_  
* support for many SDMX features including

  - generic datasets
  - data structure definitions, codelists and concept schemes
  - dataflow definitions
  - categorisations and category schemes

* pythonic representation of the SDMX information model  
* find dataflows by name or description in multiple languages if available
* read and write files including zip archives for offline use
* writer transforming SDMX generic datasets into multi-indexed pandas DataFrames or Series of observations and attributes 
* extensible through custom readers and writers for alternative input and output formats of data and metadata

Example
---------



    >>> from pandasdmx import Request
    >>> # Get annual unemployment data from Eurostat
    >>> une_resp = Request('ESTAT').get(resource_type = 'data', resource_id = 'une_rt_a')
    >>> # From the received dataset, select the time series on Greece, Ireland and Spain, and write them to a pandas DataFrame
    >>> une_df = une_resp.write(s for s in une_resp.msg.data.series if s.key.GEO in ['EL', 'ES', 'IE'])
    >>> # Explore the DataFrame
    >>> une_df.columns.names
    >>> une_df.columns.levels[0:2]
    >>> une_df.loc[:'2006', ('TOTAL', 'T')]


pandaSDMX Links
-------------------------------

* `Download the latest stable version from the Python package index <https://pypi.python.org/pypi/pandaSDMX>`_
* `Documentation <http://pandasdmx.readthedocs.org>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
 
  
  
Recent changes 
========================

Version 0.2.1 (2015-04-22)
----------------------------------

* API: add support for zip archives received from an SDMX server. 
  This is common for large datasets from Eurostat
* incidentally get a remote resource if the footer of a received message
  specifies an URL. This pattern is common for large datasets from Eurostat.
* allow passing a file-like object to api.Request.get() 
* enhance documentation
* make pandas writer parse more time period formats and increase its performance  
  
Version 0.2.0 (2015-04-13)
------------------------------------


This version is a quantum leap. The whole project has been redesigned and rewritten from
scratch to provide robust support for many SDMX features. The new architecture is centered around
a pythonic representation of the SDMX information model. It is extensible through readers and writers
for alternative input and output formats. 
Export to pandas has been dramatically improved. Sphinx documentation
has been added.

v0.1 (2014-09)
----------------

Initial release

 


