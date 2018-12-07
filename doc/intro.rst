.. _getting-started:

Getting started
===============

Installation
------------

Prerequisites
:::::::::::::

pandaSDMX is a pure `Python <http://www.python.org>`_ package.
As such it should run on any platform.
It requires Python 2.7, 3.4 or higher.

It is recommended to use one of the common Python distributions
for scientific data analysis such as

* `Anaconda <https://store.continuum.io/cshop/anaconda/>`_, or
* `Canopy <https://www.enthought.com/products/canopy/>`_.

Along with a current Python interpreter these Python distributions include
lots of
useful packages for data analysis.
For other Python distributions (not only scientific) see
`here <https://wiki.python.org/moin/PythonDistributions>`_.

pandaSDMX has the following dependencies:

* the data analysis library
  `pandas <http://pandas.pydata.org/>`_ which itself depends on a number of packages
* the HTTP library `requests <https://pypi.python.org/pypi/requests/>`_
* `LXML <http://www.lxml.de>`_ for XML processing.
* `JSONPATH-RW <https://pypi.python.org/pypi/jsonpath-rw>`_ for JSON processing.

Optional dependencies
:::::::::::::::::::::

* `requests-cache <https://readthedocs.io/projects/requests-cache/>`_
  allowing to cache SDMX messages in
  memory, MongoDB, Redis and more.
* `odo <odo.readthedocs.io>`_ for fancy data conversion and database export
* `IPython <http://ipython.org/>`_ is required to build the Sphinx documentation To do this,
  check out the pandaSDMX repository on github.
* `py.test <http://pytest.org/latest/>`_ to run the test suite.

Download
::::::::

From the command line of your OS, issue

* ``conda install -c alcibiade pandasdmx`` if you are using Anaconda,
* ``pip install pandasdmx`` otherwise.

Of course, you can also download the tarball from the PyPI and issue
``python setup.py install`` from the package dir.

Running the test suite
----------------------

From the package directory, issue the folloing command::

    >>> py.test

What next?
----------

The following chapters explain the key characteristics of SDMX,
demonstrate the basic usage of pandaSDMX and provide additional information
on some advanced topics. While users that are new to SDMX
are likely to benefit a lot from reading the next chapter on SDMX,
normal use of pandaSDMX should not strictly require this.
The :ref:`Basic usage <basic-usage>` chapter should enable you to retrieve datasets and write them to pandas
DataFrames. But if you want to exploit the full richness of the
information model, or simply feel more comfortable if you know what happens behind the scenes,
the :ref:`SDMX introduction <sdmx-tour>` is for you. It also
contains links to reference materials on SDMX. .
