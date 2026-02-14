Installation
============

Required dependencies
---------------------

pandaSDMX is a pure `Python <https://python.org>`_ package requiring Python 3.9 or higher, which can be installed:

- from `the Python website <https://www.python.org/downloads/>`_, or
- using a scientific Python distribution that includes other packages useful
  for data analysis, such as
  `Anaconda <https://store.continuum.io/cshop/anaconda/>`_,
  `Canopy <https://www.enthought.com/products/canopy/>`_, or
  others listed on `the Python wiki
  <https://wiki.python.org/moin/PythonDistributions>`_.

pandaSDMX also depends on:

- `pandas <http://pandas.pydata.org>`_ for data structures,
- `pydantic 2.x <https://docs.pydantic.dev>`_ to implement the IM,
- `requests <https://pypi.python.org/pypi/requests/>`_ for HTTP requests, and
- `lxml <http://www.lxml.de>`_ for XML processing.

Optional dependencies for extra features
----------------------------------------

- for ``cache``, allowing the caching of SDMX messages in memory, MongoDB,
  Redis, and more: `requests-cache <https://requests-cache.readthedocs.io>`_.
- for ``schema``, allowing validation of SDMXML messages against the XML schemas
  included in section 3b of the SDMX 2.1 standard: 
  `appdirs <https://pypi.org/project/appdirs>`_.
- for ``doc``, to build the documentation: `sphinx <https://sphinx-doc.org>`_
  and `IPython <https://ipython.org>`_.
- for ``test``, to run the test suite: `pytest <https://pytest.org>`_,
  `requests-mock <https://requests-mock.readthedocs.io>`_.

Instructions
------------

0. (optional) If using a `conda environment
   <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html>`_, 
   use ``source activate [ENV]`` to
   activate the
   environment in which to install pandaSDMX.
1. From the command line, issue::

     $ pip install pandasdmx
   
   or optionally from a conda environment::

     $ conda install pandasdmx -c conda-forge     


2. To also install optional dependencies, use commands like::

     $ pip install pandasdmx[cache]             # just requests-cache
     $ pip install pandasdmx[cache,doc,test]  # all extras

From source
~~~~~~~~~~~

1. Download the latest code:

   - `from PyPI <https://pypi.org/project/pandaSDMX/#files>`_,
   - `from Github <https://github.com/dr-leo/pandaSDMX>`_ as a zip archive, or
   - by cloning the Github repository::

     $ git clone git@github.com:dr-leo/pandaSDMX.git

2. In the package directory, issue::

     $ pip install  .

   or::

      $ flit install
    
.. note:: The build process adheres to 
   `PEP 517 <https://www.python.org/dev/peps/pep-0517/>`_
   using `flit <https://flit.readthedocs.io/en/latest/>`_ as build backend.  


Running tests
-------------

As per v1.1.0, the test suite is no longer packaged with any pandaSDMX distribution.
You can run it anyway by installing the  source from Github, including the ``tests`` optional dependencies.
Then, in the package directory, issue::

    $ pytest

By default, tests that involve retrieving data over the network are skipped. To
run these tests, use::

    $ pytest -m network

.. note:: Many tests requesting data or metadata from SDMX data providers 
    are out of sync with either the data provided 
    or with the source code. So expect a lot  of failures when
    running tests with the `-m network` option.

pytest offers many command-line options to control test invocation; see ``py.test --help`` or the `documentation <https://pytest.org>`_.
