pandaSDMX: Statistical Data and Metadata eXchange in Python
=============================================================


pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ 
package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <http://www.sdmx.org>`_ format. 
It supports out of the box 
the SDMX services of the European statistics office (Eurostat), 
the European Central Bank (ECB), the French National Institute for statistics (INSEE), and the OECD (JSON only). 
pandaSDMX can export data and metadata as `pandas <http://pandas.pydata.org>`_ DataFrames, 
the gold-standard 
of data analysis in Python. 
From pandas you can export data and metadata to Excel, R and friends. As from version 0.4, 
pandaSDMX can export data to many other file formats and
database backends via `Odo <http://odo.readthedocs.io/>`_. 

Main features
---------------------

* support for many SDMX features including

  - generic data sets in SDMXML format
  - compact data sets in SDMXJSON format (OECD only) 
  - data structure definitions, code lists and concept schemes
  - dataflow definitions and content-constraints
  - categorisations and category schemes

* pythonic representation of the SDMX information model  
* When requesting datasets, validate column selections against code lists 
  and content-constraints if available
* export data and structural metadata such as code lists as multi-indexed pandas DataFrames or Series, and
  many other formats and database backends via `Odo`_ 
* read and write SDMX messages to and from local files 
* configurable HTTP connections
* support for `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ allowing to cache SDMX messages in 
  memory, MongoDB, Redis or SQLite  
* extensible through custom readers and writers for alternative input and output formats of data and metadata
* growing test suite

Example
---------

Suppose we want to analyze annual unemployment data for some European countries. All we need to know
in advance is the data provider, eurostat. pandaSDMX makes it super easy to
search the directory of dataflows, and the complete structural metadata about the datasets
available through the selected dataflow. We will skip this step here.
The impatient reader may directly jump to :ref:`basic-usage`. 
The dataflow with the ID 'une_rt_a' contains the data we want. The dataflow definition references a 
datastructure definition with the ID 'DSD_une_rt_a'. 
It contains or references all the metadata describing data sets available through this dataflow: the dimensions, 
concept schemes, and corresponding code lists. 
 
.. ipython:: python

    from pandasdmx import Request
    estat = Request('ESTAT')
    # Download the metadata and expose it as a dict mapping resource names to pandas DataFrames
    metadata = estat.datastructure('DSD_une_rt_a').write()
    # Show some code lists
    metadata.codelist.ix[['AGE', 'UNIT']]
    
Next we download a data set. We use codes from the code list 'GEO'
to obtain data on Greece, Ireland and Spain only.

.. ipython:: python

    resp = Request('ESTAT').data('une_rt_a', key={'GEO': 'EL+ES+IE'}, params={'startPeriod': '2007'})
    # We use a generator expression to narrow down the column selection 
    # and write these columns to a pandas DataFrame
    data = resp.write((s for s in resp.data.series if s.key.AGE == 'TOTAL'))
    # Explore the data set. First, show dimension names
    data.columns.names
    # and corresponding dimension values
    data.columns.levels
    # Show aggregate unemployment rates across ages and sexes as
    # percentage of active population 
    data.loc[:, ('PC_ACT', 'TOTAL', 'T')]


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

