    
    
Basic usage
===============


Suppose we wanted to conduct some research on the European dairy industry.  
We look for relevant data from Eurostat, 
the European statistics office. It provides about 5700 dataflows on 28 EU countries and more. 

We import pandasdmx as follows: 

.. ipython:: python

    from pandasdmx import Request # we could have imported '*' as well
    estat = Request('ESTAT')
    # 'ESTAT' is called an atency ID. Each SDMX data provider has one.
    # The supported agencies are hard-coded in a dict containing
    # enough information to emit requests to each agency.
    # The following agencies are supported:
    estat._agencies.keys() 


Next, we select dataflows whose title (description) contains the word 'milk'.

>>> milk_table = db.execute('CREATE TABLE milk AS SELECT * FROM ESTAT_dataflows WHERE title LIKE "%milk%"')
>>> milk_list = milk_table.fetchall()

'milk_list' is a list of sqlite3.Row instances. They allow dict-like access using column names:

>>> milk_list[1]['title']
"Cows'milk collection and products obtained - annual data"
>>> cows_milk = milk_list[1]
>>> cows_milk['flowref']
'apro_mk_cola'      


Step 3: Get human-readable descriptions of the content metadata
-----------------------------------------------------------------------------
    
The complete set of structural metadata is annotated in natural language 
in so-called code-lists. You can download them as follows:

>>> milk_codes = estat.get_codes(cows_milk)
>>> milk_codes
OrderedDict([('FREQ', {'Q': 'Quarterly', 'W': 'Weekly', 'H': 'Semi-annu
al', 'M': 'Monthly', 'A': 'Annual', 'D': 'Daily'}), ('GEO', {'FI': 'Finland', 'E
S': 'Spain', 'DK': 'Denmark', 'BG': 'Bulgaria', 'FR': 'France', 'MT': 'Malta', ' [omitted]

'milk_codes' is an OrderdDict whose keys are the dimensions of the metadata.
Each value is a dict mapping possible values to human-readable descriptions.
type 'list(milk_codes.keys())' to obtain the order of the codes. 
However, note that these keys are
not ordered correctly as this feature has yet to be implemented. 
Otherwise we could have used the order to
construct a filter to download only some series from the large dataset, e.g. only series
on a small group of countries or milk products. To work around this, you can look up the 
correct order of keys in the data-browser on Eurostat's website. 
Once you know the right order, you can pass a filter string 
of the form 'val1.val2.val3...' 
to the get_data method. Here, we will simply download
the entire dataset as shown in the next step.


Step 4: Download the dataset into a pandas DataFrame or a list of pandas series
-------------------------------------------------------------------------------

We shall use the get_data() method to actually download a dataset referenced by 
a flowref or a Row instance
containing a key named 'flowref' as shown above. 

>>> df, md = estat.get_data(cows_milk, '', concat = True)
>>> df.shape
(46, 492)
>>> df.columns.names
FrozenList(['GEO', 'PRODMILK'])

Note that the first level of the column index distinguishes groups of columns by country and regions such as EU25, while the
second orders the series on a given country or region by milk product. 

get_data() returns
a 2-tuple: its first element is either a list of pandas timeseries 
(concat = False) or a DataFrame (if concat = True). The structural metadata
attached to the data is used to create a 
multi-level a.k.a. hierarchical column index for the DataFrame. 
When returning a list of timeseries, their 'name' attributes contain the non-global metadata as
NamedTuples.
The second element of the 2-tuple is a dict
containing global metadata describing the entire dataset. As each global key by definition takes on only one value,
it is unsuitable to structure the data. Hence, it is disregarded when creating the column index.

The second argument of get_data() (here: an empty string) could be used to narrow down the datasets using structural
metadata. E.g., '...NL' would yield data solely on the Netherlands. 
     

Step 5: Analyze the data with pandas
----------------------------------------------
  
The plain language descriptions obtained by calling the 'get_codes' method 
allow you to select relevant columns in pandas. Be sure to read the
`pandas docs <http://pandas.pydata.org/pandas-docs/stable/>`_, specifically on 
hierarchical indexing and time series.
  
>>> df, md = estat.get_data(cows_milk, '', concat=True)
>>> md 
{'FREQ': 'A', 'UNIT': 'THS_T'}

Hence all series have annual data. The unit is "thousand tons".

>>> cheese_fr = df[('FR', 'MM241')]
>>> cheese_de = df[('DE', 'MM241')]

>>> cheese_de.head()
2013-01-01    2258
2012-01-01    2240
2011-01-01    2196
2010-01-01    2169
2009-01-01    2086
Name: (DE, MM241), dtype: float64

Above we have used dict-like syntax. But pandas even allows attribute-like column selection:
    
>>> ratio = df.FR.MM241 / df.DE.MM241
>>> ratio.head()
2013-01-01    0.810895
2012-01-01    0.811161
2011-01-01    0.819672
2010-01-01    0.829876
2009-01-01    0.820709
dtype: float64

