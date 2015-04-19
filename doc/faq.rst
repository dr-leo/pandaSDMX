FAQ
======


Can pandaSDMX connect to SDMX providers other than ECB and Eurostat? 
-----------------------------------------------------------------------

Any SDMX provider can be supported that generates SDMX 2.1-compliant 
messages. The only agencies I know of that deliver data in this format 
are ECB and Eurostat.
Support for SDMX 2.0 messages could be added as a new reader module. Perhaps the model would have to be tweaked a bit as well.

Writing large datasets to pandas DataFrames is slow. What can I do?
----------------------------------------------------------------------------

The main performance hit comes from parsing the time or time period strings. In case of regular data such as monthly (not trading day!), call the
``write``  method with ``fromfreq``  set to True so that only the first string will be parsed and the rest inferred from the
frequency of the series. Caution: If the series is stored in the XML document in reverse chronological order,
the ``reverse_obs``  argument must be set to True as well to prevent the resulting dataframe index from extending into a remote future.
 