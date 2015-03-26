
Welcome to the pandaSDMX documentation!
==========================================


.. caution::

    This documentation is under construction and not yet intended for use. 


pandaSDMX is a Python package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <www.sdmx.org>`_ format. It works well with the SDMX services of the European statistics office (Eurostat)
and the European Central Bank (ECB). While pandaSDMX is extensible to 
cater any output format, it currently supports only `pandas <pandas.pydata.org>`_, the gold-standard 
for data analysis in Python. 

The shortest code example to download a dataset from Eurostat might look like this:

.. ipython:: python

    from pandasdmx import Request
    df = Request('ESTAT').get(resource_type = 'data', resource_id = 'une_rt_a').write()
   
The resulting pandas DataFrame contains annual unemployment data for the EU by age and sex.   
The rest is poor man's pandas magic:
  
.. ipython:: python

    df.shape
    df.columns.names
    df.columns.levels[0]
    df.xs(('TOTAL', 'T' ,'HR'), level=('AGE','SEX', 'GEO'), axis=1).head()

Main features:

* simple Request API inspired by python-requests
* pythonic representation of the SDMX information model as thin layer on top of the LXML element tree
* transforms multidimensional datasets into multi-indexed pandas DataFrames or pandas Series 
* extensible through readers and writers for alternative input and output formats of data and metadata
* relies on best-of-breed libraries such as rrequests and lxml


 
Contents:

.. toctree::
    :maxdepth: 2

    intro
    usage
    api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

