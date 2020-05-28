pandaSDMX: Statistical Data and Metadata eXchange
=================================================

.. image:: https://travis-ci.com/dr-leo/pandaSDMX.svg?branch=master
   :target: https://travis-ci.com/dr-leo/pandaSDMX
   :alt: Travis-CI status
.. image:: https://codecov.io/gh/dr-leo/pandaSDMX/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/dr-leo/pandaSDMX
   :alt: Codecov status
.. image:: https://readthedocs.org/projects/pandasdmx/badge/?version=latest
   :target: https://pandasdmx.readthedocs.io/en/latest
   :alt: Documentation Status
.. image:: https://img.shields.io/pypi/v/pandaSDMX.svg
   :target: https://pypi.org/project/pandaSDMX
   :alt: PyPI
.. image:: https://img.shields.io/conda/dn/conda-forge/pandasdmx.svg
   :target: https://github.com/conda-forge/pandasdmx-feedstock
   :alt: conda-forge

`Source code @ Github <https://github.com/dr-leo/pandasdmx/>`_ —
`Authors <AUTHORS>`_

**pandaSDMX** is an `Apache 2.0-licensed <LICENSE>`_ Python package that
implements `SDMX <http://www.sdmx.org>`_ 2.1 (`ISO 17369:2013
<https://www.iso.org/standard/52500.html>`_), a format for exchange of
**statistical data and metadata** used by national statistical agencies,
central banks, and international organisations.

**pandaSDMX** can be used to:

- explore the data available from `data providers
  <https://pandasdmx.readthedocs.io/en/latest/sources.html>`_
  such as the World Bank, ILO, ECB, Eurostat, OECD, and United Nations;
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

* stable: https://pandasdmx.readthedocs.io/ 
* latest: https://pandasdmx.readthedocs.io/en/latest  or
* v0.9: https://pandasdmx.readthedocs.io/en/v0.9 for the 0.9 release.


License
-------

Copyright 2014–2020, `pandaSDMX developers <AUTHORS>`_

Licensed under the Apache License, Version 2.0 (the “License”); you may not use
these files except in compliance with the License. You may obtain a copy of the
License:

- from the file LICENSE included with the source code, or
- at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

