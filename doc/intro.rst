.. _getting-started:

Getting started
===============


Installation
--------------------------------------------------

Prerequisites
:::::::::::::::::::::::::::::::::::::::

pandaSDMX is a pure `Python <http://www.python.org>`_ package. 
As such it should run on any platform. 
It requires Python 2.7, 3.4 or 3.5. Python 3.3 should work as well, 
but this is untested. 

It is recommended to use one of the common Python distributions
for scientific data analysis such as
 
* `Anaconda <https://store.continuum.io/cshop/anaconda/>`_, or
* `Canopy <https://www.enthought.com/products/canopy/>`_. 

Along with a current Python interpreter these Python distributions include 
the dependencies as well as lots of
other useful packages for data analysis.   
For other Python distributions (not only scientific) see
`here <https://wiki.python.org/moin/PythonDistributions>`_.  

pandaSDMX has the following dependencies:

* the data analysis library  
  `pandas <http://pandas.pydata.org/>`_ which itself depends on a number of packages
* the HTTP library `requests <https://pypi.python.org/pypi/requests/>`_
* `LXML <http://www.lxml.de>`_ for XML processing. 

Optional dependencies
::::::::::::::::::::::::::::::::::::::::::

* `requests-cache <https://readthedocs.io/projects/requests-cache/>`_ 
  allowing to cache SDMX messages in 
  memory, MongoDB, Redis and more.
* `odo <odo.readthedocs.io>`_ for fancy data conversion and database export
* `IPython <http://ipython.org/>`_ is required to build the Sphinx documentation To do this,
  check out the pandaSDMX repository on github.  
* `py.test <http://pytest.org/latest/>`_ to run the test suite.

Download
:::::::::::::::::::::::::::

You can download and install pandaSDMX like any other Python package, e.g.

* from the command line with ``pip install pandasdmx``, or 
* manually by `downloading <https://pypi.python.org/pypi/pandaSDMX/>`_ and unzipping the latest source distribution.
  From the package directory you should then issue the command ``python setup.py install``. 

Running the test suite
---------------------------------------------------------
 
From the package directory, issue the folloing command::
 
    >>> py.test

    
Package overview
------------------

.. rubric:: Modules

api 
    module containing the API to make queries to SDMX web services. 
    See :class:`pandasdmx.api.Request` in particular its `get` method.
    :meth:`pandasdmx.api.Request.get`  return :class:`pandasdmx.api.Response` instances.
model 
    implements the SDMX information model. 
remote 
    contains a wrapper class around ``requests`` for http. 
    Called by :meth:`pandasdmx.api.Request.get` to make
    http requests to SDMX services. Also reads sdmxml files instead of querying them over the web.

.. rubric:: Subpackages

reader 
    read SDMX files and instantiate the appropriate classes from :mod:`pandasdmx.model` 
    There is only one reader for XML-based SDMXML v2.1. Future versions may add reader modules for other formats.
writer 
    contains writer classes transforming SDMX artefacts into other formats or
    writing them to arbitrary destinations such as databases. The only available 
    writer for now writes generic datasets to pandas DataFrame or Series.
utils: 
    utility functions and classes. Contains a wrapper around :class:`dict` allowing attribute access to dict items.
tests 
    unit tests and sample files


What next?
--------------

The remaining chapters explain the key characteristics of SDMX, 
demonstrate the basic usage of pandaSDMX and provide additional information 
on some advanced topics. While users that are new to SDMX 
are likely to benefit a lot from reading the next chapter on SDMX,
normal use of pandaSDMX should not strictly require this. 
The :ref:`Basic usage <basic-usage>` chapter should enable you to retrieve datasets and write them to pandas
DataFrames. But if you want to exploit the full richness of the
information model, or simply feel more comfortable if you know what happens behind the scenes, 
the :ref:`SDMX introduction <sdmx-tour>` is for you. It also
contains links to authoratative SDMX resources. 



 