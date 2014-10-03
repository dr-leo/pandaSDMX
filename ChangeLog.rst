Change log
========================

v0.2dev
==========

* use sdmx 2.1 for ECB queries
* generate PeriodIndex if FREQ is known
* parse date ranges such as '2010-Q4' and '2014-S1'
* get_data: no longer remove global codes from Series.name
  when returning list of Series
* attach global codes to DataFrame by setting
  a custom metadata attribute. In v0.1.2, global metadata was returned as a separate dict
* refactor get_data to delegate parsing of xml tree to a separate
  parse_data generator function. 
  



v0.1.2 (2014-09-17)

* fix xml encoding. This brings dramatic speedups when downloading and parsing data
* extend description.rst


Version 0.1 (2014-09-07)

initial release
