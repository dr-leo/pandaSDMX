Home
==========================================


pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ 
package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <http://www.sdmx.org>`_ format. 
It works well with the SDMX services of the European statistics office (Eurostat)
and the European Central Bank (ECB). While pandaSDMX is extensible to 
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
* read and write local files for offline use 
* writer transforming SDMX generic datasets into multi-indexed pandas DataFrames or Series of observations and attributes 
* extensible through custom readers and writers for alternative input and output formats of data and metadata

Example
---------


.. ipython:: python

    from pandasdmx import Request
    # Get annual unemployment data from Eurostat
    une_resp = Request('ESTAT').get(resource_type = 'data', resource_id = 'une_rt_a')
    # From the received dataset, select the time series on Greece, Ireland and Spain, and write them to a pandas DataFrame
    une_df = une_resp.write(s for s in une_resp.msg.data.series if s.key.GEO in ['EL', 'ES', 'IE'])
    # Explore the DataFrame
    une_df.columns.names
    une_df.columns.levels[0:2]
    une_df.loc[:'2006', ('TOTAL', 'T')]


pandaSDMX Links
-------------------------------

* `Download the latest stable version from the Python package index <https://pypi.python.org/pypi/pandaSDMX>`_
* `Documentation <http://pandasdmx.readthedocs.org>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
 
 
Table of contents
---------------------


.. toctree::
    :maxdepth: 2
    :numbered:

    whatsnew
    faq
    intro
    sdmx_tour
    usage
    advanced
    API documentation <api/modules>
    license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

