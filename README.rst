pandaSDMX: Statistical Data and Metadata eXchange
=================================================

.. image:: https://travis-ci.org/dr-leo/pandaSDMX.svg?branch=master
   :target: https://travis-ci.org/dr-leo/pandaSDMX
.. image:: https://codecov.io/gh/dr-leo/pandaSDMX/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/dr-leo/pandaSDMX
.. image:: https://readthedocs.org/projects/pandasdmx/badge/?version=latest
   :target: https://pandasdmx.readthedocs.io/en/latest
   :alt: Documentation Status
.. image:: https://img.shields.io/pypi/v/pandaSDMX.svg
   :target: https://pypi.org/project/pandaSDMX

| Author: Dr. Leo <fhaxbox66@gmail.com>
| https://github.com/dr-leo/pandasdmx/

``pandaSDMX`` is an `Apache 2.0-licensed <LICENSE.txt>`_ Python library that implements `SDMX <http://www.sdmx.org>`_ 2.1,
(`ISO 17369:2013 <https://www.iso.org/standard/52500.html>`_), a format for
exchange of **statistical data and metadata** used by national statistical
agencies, central banks, and international organisations.

``pandaSDMX`` can be used to:

- explore the data available from
  `data providers <https://pandasdmx.readthedocs.io/en/latest/sources.html>`_
  such as the World Bank, International Monetary Fund, Eurostat, OECD, and United Nations;
- parse data and metadata in SDMX-ML (XML) or SDMX-JSON formats—either:

  - from local files, or
  - retrieved from SDMX web services, with query validation and caching;

- convert data and metadata into `pandas <https://pandas.pydata.org>`_ objects,
  for use with the analysis, plotting, and other tools in the Python data
  science ecosystem;
- apply the `SDMX Information Model
  <https://pandasdmx.readthedocs.io/en/latest/im.html>`_ to your own data;

…and much more.


Documentation
-------------

See https://pandasdmx.readthedocs.io/en/latest for the latest docs, or
https://pandasdmx.readthedocs.io/en/v0.9 for the 0.9 release.


History
-------

pandaSDMX originally started as a fork of pysdmx_. Even if pandaSDMX would not
have been possible without the inspiring work done for that project, the author
decided to rewrite it from scratch, so pandaSDMX became an independent project.
Many people from all over the world have generously contributed code and
feedback.

pandaSDMX also contains sample data and metadata from the SDMX user guide.

.. _pysdmx: https://github.com/widukind/pysdmx
.. _aadict: https://github.com/metagriffin/aadict
