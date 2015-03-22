=============
pandaSDMX
=============





.. contents::


1. About pandaSDMX
=============================
 
pandaSDMX is an `SDMX <http://www.sdmx.org/>`_ 
client that allows the retrieval, acquisition, and processing of datasets
and corresponding metadata provided through web services complying with SDMX 2.1.

What pandaSDMX can do for you
--------------------------------------------

Data and metadata is exposed as a pythonic representation of the SDMX 
information model.  

SDMX data providers
--------------------------------

SDMX data and metadata are provided by national statistics offices, 
central banks and international organisations. 
Notable SDMX data providers are
 
* `Eurostat <https://webgate.ec.europa.eu/fpfis/mwikis/sdmx/index.php/Main_Page>`_,
* the `European Central Bank <http://www.ecb.europa.eu/stats/services/sdmx/html/index.en.html>`_, 
* the `Bank for International Settlements <http://www.bis.org/statistics/sdmx.htm>`_, 
* the `International Monetary Fund <http://sdmxws.imf.org/IMFStatWS_SDMX2/sdmx.asmx>`_, and
* the `OECD <http://stats.oecd.org/SDMXWS/sdmx.asmx>`_
* the International Lator Orgsnisation. 
 
However, some data providers support older SDMX standards or only parts of SDMX 2.1. 
At present, pandaSDMX
can query datasets and metadata vom Eurostat, the ECB and ILO. 
 
 Features
 pandaSDMX exposes datasets as pandas time series or DataFrames with hierarchical indexes created from structural metadata.
 
  

2. Installation
===================

pandaSDMX contains the pure Python module 'pandasdmx'. You can install it
with "pip install pandasdmx" or manually by downloading and extracting the source distribution, 
and issuing "python setup.py install" from the command line.

pandaSDMX has the following dependencies:

* the data analysis library  
  `pandas <http://pandas.pydata.org/>`_ which itself depends on a number of packages
* `requests <https://pypi.python.org/pypi/requests/>`_
* `LXML <https://pypi.python.org/pypi/lxml/>`_ 

Instead of pip-installing the dependencies, it is recommended to use a Python distribution
for scientific computing and data analysis such as 
`Anaconda <https://store.continuum.io/cshop/anaconda/>`_ or
`Canopy <https://www.enthought.com/products/canopy/>`_. 
Scientific Python distributions include, 
among many other useful things, the interactive Python shell `IPython <http://ipython.org/>`_ 
which is a must-have when working with data. 
For other Python distributions (not only scientific) see
`here <https://wiki.python.org/moin/PythonDistributions>`_.  
  
  
4. Known issues, ToDo's
====================================== 
  
While pandasdmx works well with Eurostat data, other institutions cause problems. Moreover, content metadata
such as on data quality is currently ignored. So are categories, i.e. folders of dataflows; they are considered as a flat list. 
For other features such as writing data to a local file, see the doc strings of the get_data and get_dataflows methods. 
 
For a more detailed ToDo list consider the ToDo.rst file in the source distribution.

5. How to contribute
======================

Development takes place on github. Feel free to file an
`issue <https://github.com/dr-leo/pandaSDMX/issues>`_.  
The author welcomes feedback by `e-mail <fhaxbox66@gmail.com>`_.  
  
  
6. Recent changes 
========================

Version 0.1.2 (2014-09-17)

* fix xml encoding. This brings dramatic speedups when downloading and parsing data
* extend tutorial

The complete changelog is part of the source distribution.
