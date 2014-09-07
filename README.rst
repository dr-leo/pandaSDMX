pandaSDMX
===========

Description: A Python- and pandas-powered client for statistical data and metadata exchange
Author: Dr. Leo <fhaxbox66@gmail.com>
License: GPL
Development website: https://github.com/dr-leo/pandasdmx/


Purpose of this project
 ====================
 
 pandaSDMX is an endeavor to create an SDMX client that facilitates the management, acquisition and analysis of datasets
 made available via SDMX 2.0 or 2.1. Data is made available through pandas time series or DataFrames.
 Dataflow information is stored in a relational database. Currently, only SQLite is supported.
  
  For further information read the description.rst file. After the first release this file is also
  available in HTML format on http://pypi.python.org/.
  
  Acknowledgements
  ===============
  
  pandaSDMX started as a fork of
  https://github.com/widukind/pysdmx. 
  The Widukind team contributed the code for reading the xml files and gleening the actual data. pandaSDMX would not exist
  without this great contribution. However, as development of pysdmx has slowed down over the summer,
  the author took over and added a number of features, in particular the construction of hierarchically indexed dataframes using
  structural metadata.
  
   