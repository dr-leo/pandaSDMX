pysdmx
======

Python interface to SDMX

Installation
------------

For the time being, pysdmx is not on pypi. You can use the standard procedure from distutils.

    python3 setup.py sdist
    python3 setup.py install

Usage
-----

pysdmx provides a bookmark for the SDMX endpoint provided by Eurostat.

    >>>import pysdmx
    >>>data = pysdmx.eurostat.data_extraction('cdh_e_fos','..PC.FOS1.BE','2005','2011')
    >>>data.time_series
