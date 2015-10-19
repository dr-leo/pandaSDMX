pandaSDMX: Statistical Data and Metadata eXchange in Python
=============================================================


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
  - data structure definitions, code lists and concept schemes
  - dataflow definitions and content-constraints
  - categorisations and category schemes

* pythonic representation of the SDMX information model  
* find dataflows by name or description in multiple languages if available
* When requesting datasets, validate column selections against code lists 
  and content-constraints if available 
* read and write SDMX messages to and from local files 
* configurable HTTP connections
* support for `requests-cache <https://readthedocs.org/projects/requests-cache/>`_ allowing to cache SDMX messages in 
  memory, MongoDB, Redis or SQLite  
* writer transforming SDMX generic datasets into multi-indexed pandas DataFrames or Series of observations and attributes 
* extensible through custom readers and writers for alternative input and output formats of data and metadata

Example
---------


.. ipython:: python

    from pandasdmx import Request
    # Get recent annual unemployment data on Greece, Ireland and Spain from Eurostat
    resp = Request('ESTAT').get('data', 'une_rt_a', key={'GEO': 'EL+ES+IE'}, params={'startPeriod': '2006'})
    # From the received dataset, select the time series on all age groups and write them to a pandas DataFrame
    une_df = resp.write(s for s in resp.data.series if s.key.AGE == 'TOTAL')
    # Explore the DataFrame. First, show dimension names
    une_df.columns.names
    # corresponding dimension values
    une_df.columns.levels
    # Print aggregate unemployment rates across ages and sexes 
    une_df.loc[:, ('TOTAL', 'T')]


pandaSDMX Links
-------------------------------

* `Download the latest stable version from the Python package index <https://pypi.python.org/pypi/pandaSDMX>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
* `Official SDMX website <http://www.sdmx.org>`_ 
 
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
    contributing
    license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

