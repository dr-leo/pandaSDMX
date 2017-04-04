=============
pandaSDMX
=============



pandaSDMX is an Apache 2.0-licensed `Python <http://www.python.org>`_ 
package aimed at becoming the 
most intuitive and versatile tool to retrieve and acquire statistical data and metadata
disseminated in `SDMX <http://www.sdmx.org>`_ format. 
It supports out of the box 
the SDMX services of the European statistics office (Eurostat), 
the European Central Bank (ECB), and the French National Institute for statistics (INSEE). 
pandaSDMX can export data and metadata as `pandas <http://pandas.pydata.org>`_ DataFrames, 
the gold-standard 
of data analysis in Python. 
From pandas you can export data and metadata to Excel, R and friends. As from version 0.4, 
pandaSDMX can export data to many other file formats and
database backends via `Odo <odo.readthedocs.io/>`_. 

Main features
==================

* intuitive API inspired by `requests <https://pypi.python.org/pypi/requests/>`_  
* support for many SDMX features including

  - generic datasets
  - data structure definitions, code lists and concept schemes
  - dataflow definitions and content-constraints
  - categorisations and category schemes

* pythonic representation of the SDMX information model  
* When requesting datasets, validate column selections against code lists 
  and content-constraints if available
* export data and metadata as multi-indexed pandas DataFrames or Series, and
  many other formats and database backends via `Odo <odo.readthedocs.io/>`_ 
* read and write SDMX messages to and from local files 
* configurable HTTP connections
* support for `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ allowing to cache SDMX messages in 
  memory, MongoDB, Redis or SQLite  
* extensible through custom readers and writers for alternative input and output formats of data and metadata
* growing test suite

For further details including extensive code examples
see the 
`documentation <https://pandasdmx.readthedocs.io>`_ . 


pandaSDMX Links
-------------------------------

* `Documentation <https://pandasdmx.readthedocs.io>`_
* `Mailing list <https://groups.google.com/forum/?hl=en#!forum/sdmx-python>`_  
* `github <https://github.com/dr-leo/pandaSDMX>`_
 
  
