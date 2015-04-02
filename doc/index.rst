
Home
==========================================


.. caution::

    This documentation is under construction and not yet intended for use. 


pandaSDMX is a Python package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <http://www.sdmx.org>`_ format. 
It works well with the SDMX services of the European statistics office (Eurostat)
and the European Central Bank (ECB). While pandaSDMX is extensible to 
cater any output format, it currently supports only `pandas <http://pandas.pydata.org>`_, the gold-standard 
for data analysis in Python. But from pandas you can export your data to Excel and friends. 

.. rubric:: Main features:

* simple, intuitive API
* supports a growing set of SDMX features including

  - generic datasets
  - data structure definitions, codelists and concept schemes
  - dataflow definitions
  - categorisations and category schemes
  
* find dataflows by namd or description in multiple languages if available
* read and write local files for offline use 
* pythonic representation of the SDMX information model 
* writer transforming SDMX generic datasets into multi-indexed pandas DataFrames or Series of observations and attributes 
* extensible through custom readers and writers for alternative input and output formats of data and metadata

.. rubric:: Example:


The shortest code example to download a dataset from Eurostat might look like this:

.. ipython:: python

    from pandasdmx import Request
    df = Request('ESTAT').get(resource_type = 'data', resource_id = 'une_rt_a').write()
   
The resulting pandas DataFrame contains unemployment rates for the past 32 years by EU-country, age, and sex.   
The rest is poor man's pandas magic:
  
.. ipython:: python

    df.shape
    df.columns.names # dimension names
    df.columns.levels[0] # dimension values of the 'AGE' dimension
    df.xs(('TOTAL', 'T' ,'HR'), level=('AGE','SEX', 'GEO'), axis=1).head()


.. rubric:: pandaSDMX Links:

* `Python package index <https://pypi.python.org/pypi/pandaSDMX>`_
* `Documentation <http://pandasdmx.readthedocs.org>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
 
 
Table of contents
---------------------


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

