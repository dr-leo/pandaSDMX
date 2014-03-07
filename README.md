pysdmx
======

Python interface to SDMX

Usage
-----

pysdmx provides a bookmark for the SDMX endpoint provided by Eurostat.

>>>import pysdmx
>>>data = pysdmx.eurostat.data_extraction('cdh_e_fos','..PC.FOS1.BE','2005','2011')
>>>data.time_series
