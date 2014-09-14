=============
pandaSDMX
=============





.. contents::


1. Overview
====================
 
pandaSDMX is an endeavor to create an `SDMX <http://www.sdmx.org/>`_ 
client that facilitates the acquisition, management, and analysis of large datasets
disseminated according to the SDMX standard by national statistics offices, central banks and international organisations. Notable SDMX data providers are 
`Eurostat <https://webgate.ec.europa.eu/fpfis/mwikis/sdmx/index.php/Main_Page>`_,
the `European Central Bank <http://www.ecb.europa.eu/stats/services/sdmx/html/index.en.html>`_, 
the `Bank for International Settlements <http://www.bis.org/statistics/sdmx.htm>`_, 
the `International Monetary Fund <http://sdmxws.imf.org/IMFStatWS_SDMX2/sdmx.asmx>`_, and
the `OECD <http://stats.oecd.org/SDMXWS/sdmx.asmx>`_, 
to name but a few. pandaSDMX downloads datasets and exposes them as pandas time series or DataFrames with hierarchical indexes created from structural metadata.
Metadata on the content of datasets (so-called dataflows) is stored locally using SQLite. 
  

2. Installation
===================

pandaSDMX contains the pure Python module 'pandasdmx'. You can install it
with "pip install pandasdmx" or manually by downloading and extracting the source distribution, 
and issuing "python setup.py install" from the command line.

pandaSDMX has the following dependencies:

* the data analysis library  
  `pandas <http://pandas.pydata.org/>`_ which itself depends on a number of packages, and
* `requests <https://pypi.python.org/pypi/requests/>`_
* `LXML <https://pypi.python.org/pypi/lxml/>`_ 

It is recommended to use one of the pre-packaged Python distributions
for scientific computing and data analysis rather than having pip install those dependencies. 
Scientific Python distributions include, 
among many other useful things, the interactive Python shell `IPython <http://ipython.org/>`_ 
which is a must-have when working with data. The author uses 
`Anaconda <https://store.continuum.io/cshop/anaconda/>`_. 
For other Python distributions (not only scientific) see
`here <https://wiki.python.org/moin/PythonDistributions>`_.  
  
  
3. Tutorial
=============

Suppose we wanted to conduct some research on the European dairy industry. As pandaSDMX's support for FAO is still 
experimental (or indeed not working), we will look for relevant data from Eurostat, 
the European statistics office. It provides data from national statistics offices of the 28 EU countries and more. 

Step 1: Instantiate a 'Client' for Eurostat
-----------------------------------------------------------------========

..
..
::

    >>> from pandasdmx import client
    >>> estat = client('Eurostat', 'milk.db')

Here, we have used the factory function 'client'. It instantiates the 'Client' class
using the values required for Eurostat as hard-coded in 'pandasdmx.providers'.
 
Step 2: Get the available dataflows and identify interesting datasets
-----------------------------------------------------------------------

Now that we have an SDMX client for Eurostat, we call its 'get_dataflows' method
to download the complete list of dataflows. A dataflow is essentially a tuple describing
a dataset. Its main fields are a flow reference ('flowref')and a human-readable description ('title'). 
Eurostat offers about 4500 datasets. Downloading the complete
list of dataflows may take a while.   

::

    >>> db = estat.get_dataflows()
    >>> str(estat)
    "<class 'pandasdmx.Client'>('http://www.ec.europa.eu/eurostat/SDMX/diss-web/rest', 'ESTAT', db_filename = 'milk.db') Database: <sqlite3.Connection object at 0x0501A130> ['table: ESTAT_dataflows SQL: CREATE TABLE ESTAT_dataflows \\n            (id INTEGER PRIMARY KEY, agencyID text, flowref text, version text, title text); ']"

The string representation of 'Client' shows the attached SQLite database and the tables. Note
that the get_dataflows() method has just created the 'ESTAT_dataflows' table.

Next, we select dataflows whose title (description) contains the word 'milk'.

::

    >>> milk_table = db.execute('CREATE TABLE milk AS SELECT * FROM ESTAT_dataflows WHERE title LIKE "%milk%"')
    >>> milk_list = milk_table.fetchall()

'milk_list' is a list of sqlite3.Row instances. They allow dict-like access using column names:

::

    >>> milk_list[1]['title']
    "Cows'milk collection and products obtained - annual data"
    >>> cows_milk = milk_list[1]
    >>> cows_milk['flowref']
        


Step 3: Get human-readable descriptions of the content metadata
-----------------------------------------------------------------------------
    
    From 'df.columns.levels' we can see the values of the structural metadata. Their meanings are explained
    in so-called code-lists. You can download them as follows:

::
    
    >>> milk_codes = estat.get_codes(milk_list[1])
    >>> milk_codes
    Out[14]: OrderedDict([('FREQ', {'Q': 'Quarterly', 'W': 'Weekly', 'H': 'Semi-annu
    al', 'M': 'Monthly', 'A': 'Annual', 'D': 'Daily'}), ('GEO', {'FI': 'Finland', 'E
    S': 'Spain', 'DK': 'Denmark', 'BG': 'Bulgaria', 'FR': 'France', 'MT': 'Malta', ' [omitted]


Step 4: Download the dataset into a pandas datastructure
------------------------------------------------------------------

Next, we use the get_data() method to actually download a dataset referenced by a flowref or a Row instance
containing a key named 'flowref' as shown above. 

::

    >>> df, md = estat.get_data(milk_list[1], '', concat = True)
    >>> md
    {'FREQ': 'A', 'UNIT': 'THS_T'}
    >>> df.shape
    (46, 492)
    >>> df.columns.names
    FrozenList(['GEO', 'PRODMILK'])

get_data() returns
a 2-tuple: its first element is either a list of pandas timeseries (concat = False) or a DataFrame (if concat = True). The structural metadata
attached to the data is used to create a multi-level column index for the DataFrame. When returning a list of timeseries, their 'name' attributes contain the non-global metadata as
hashable NamedTuples (dicts would cause problems when concatenating the series later).
The second element of the 2-tuple is a dict
containing global metadata describing the entire dataset. As each key takes on only one value,
it is unsuitable to structure the data. Hence, it is disregarded when creating the column index.
The second argument of get_data() (here: an empty string) is used to narrow down the datasets using structural
metadata. E.g., '...NL' would yield data solely on the Netherlands.

     

Step 5: Analyze the data with pandas
  ----------------------------------------------
  
  The plain language descriptions of the metadata allows you to select relevant columns in pandas. Be sure to read the
  pandas docs, specifically on hierarchical indexing and time series.
   
4. Next steps, known issues, ToDo's
====================================== 
  
While pandasdmx works well with Eurostat data, other institutions cause problems. Moreover, content metadata
such as on data quality is currently ignored. So are categories, i.e. folders of dataflows; they are considered as a flat list. 
For other features such as writing data to a local file, see the doc strings of the get_data and get_dataflows methods. 
 
For a more detailed ToDo list consider the ToDo.rst file in the source distribution. Any help is much appreciated. 
  
  
5. Change log
========================

Version 0.1 (2014-09-07)

initial release
