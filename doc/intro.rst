

Getting started
===============


Installation
--------------------------------------------------

Prerequisites
:::::::::::::::::::::::::::::::::::::::

pandaSDMX is a pure `Python <http://www.python.org>`_ package. As such it should run on any platform. 
It requires Python 2.7 or 3.4. Python 3.3 should work as well, but this is untested.

pandaSDMX has the following dependencies:

* the data analysis library  
  `pandas <http://pandas.pydata.org/>`_ which itself depends on a number of packages
* `requests <https://pypi.python.org/pypi/requests/>`_
* `LXML <http://www.lxml.de>`_ 

Optional dependencies
::::::::::::::::::::::::::::::::::::::::::

* `IPython <http://ipython.org/>`_ is required to build the Sphinx documentation To do this,
  check out the pandaSDMX repository on github.  
* `nose <https://pypi.python.org/pypi/nose>`_ to run the test suite.

It is probably a good idea to use one of the common Python distributions
for scientific data analysis such as
 
* `Anaconda <https://store.continuum.io/cshop/anaconda/>`_, or
* `Canopy <https://www.enthought.com/products/canopy/>`_. 

Along with a current Python interpreter these Python distributions include, 
the dependencies as well as lots of
other useful packages.   
For other Python distributions (not only scientific) see
`here <https://wiki.python.org/moin/PythonDistributions>`_.  

Download
:::::::::::::::::::::::::::

You can download and install pandaSDMX like any other Python package, e.g.

* from the command line with ``pip install pandasdmx``, or 
* manually by `downloading <https://pypi.python.org/pypi/pandaSDMX/>`_ and unzipping the latest source distribution.
  From the package directory you should then issue the command ``python setup.py install``. 

Running the test suite
==============================================  
 
 From the package directory, issue the folloing command::
 
    nosetests pandasdmx

 
A very brief introduction to SDMX
====================================

Overall purpose
--------------------------------------------------------------

`SDMX <http://www.sdmx.org>`_ (short for: Statistical Data and Metadata eXchange)
is a set of `standards and guidelines <http://sdmx.org/?cat=5>`_
aimed at facilitating the production, dissemination, retrieval and
processing of statistical data and metadata.
SDMX is sponsored by a wide range of public institutions including the UN, the IMF, the Worldbank, BIS, ILO, FAO, 
the OECD, the ECB, Eurostat, and a number of national statistics offices. These and other institutions
provide a vast array of current and historic datasets and metadatasets via free or fee-based REST and SOAP web services. 
pandaSDMX only supports SDMX v2.1, that is, the latest version of this standard. Some agencies such as the IMF continue to offer SDMX 2.0-compliant services.
These cannot be accessed by pandaSDMX. 
While this may change in future versions, there is the expectation that SDMX providers will upgrade to the latest standards at some point.  
 
Information model
----------------------------------------------------------------

At its core, SDMX defines an :index:`information model` consisting of a set of :index:`classes`, their logical relations, and semantics.
There are classes defining things like datasets, metadatasets, data and metadata structures, 
processes, organisations and their specific roles to name but a few. The information model is agnostic as to its
implementation. Luckily, the SDMX standard provides an XML-based implementation (see below). And
a JSON-variant is in the works.
 
The following sections briefly introduces some key elements of the information model.

Datasets
::::::::::::::::::::::::::::::::::::::::::::

a :index:`dataset` can broadly be described as a
container of ordered :index:`observations` and :index:`attributes` attached to them. Observations (e.g. the annual unemployment rate) are classified 
by :index:`dimensions` such as country, age, sex, and time period. Attributes may further describe an individual observation or
a set of observations. Typical uses for attributes are the level of confidentiality, or data quality. 
Observations may be clustered into :index:`series`, in particular, time series. The dataset
must explicitly specify the :index:`dimension at observation` such as 'time', 'time_period' or anything else. 
If a dataset consists of series whose
dimension at observation is neither time nor time period, the dataset is called :index:`cross-sectional`. 
A dataset that is not grouped into series, i.e.
where all dimension values including time, if available, are stated for each observation, are called :index:`flat datasets`. Thes are not 
memory-efficient, but benefit from a very simple representation.  

An attribute may be attached to a series to express
the fact that it applies to all contained observations. This increases 
efficiency and adds meaning. Subsets of series within a dataset may be clustered into :index:`groups`. 
A group is 
defined by specifying one or more dimension values, but not all: At least the dimension at observation and one other
dimension must remain free (or wild-carded). Otherwise, the group would in fact be either a single observation or a series.
The main purpose of :index:`group` is to 
serve as another attachment point for attributes. Hence, a given attributes may be attached to all series
within the group at once. Attributes may finally be attached to the entire dataset, i.e. to all observations therein. 
 
Structural metadata: data structure definition, concept scheme and code list
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
In the above section on datasets, we have carelessly used structural terms such as dimension, dimension value and
attachment of attributes. This is because it is almost impossible to talk about datasets without talking about their structure. The information model 
provides a number of classes to describe the structure of datasets without talking about data. The container class for this is called
:index:`DataStructureDefinition` (in short: :abbr:`DSD`). It contains a list of dimensions and for each dimension a reference to exactly one
:index:`concept` describing its meaing. A concept describes the set of permissible dimension values. This can
be done in various ways depending on the intended data type. Finite value sets (such as country codes, currencies, a data quality classification etc.) are
described by reference to :index:`code lists`. Infinite value sets are described by :index:`facets` which is simply a
way to express that a dimension may have int, float or time-stamp values, to name but a few. A set of concepts referred to in the
dimension descriptors of a data structure definition is called :index:`concept scheme`.

The set of allowed observation values such as the unemployment rate measured in per cent is 
defined by a special dimension: the :index:`MeasureDimension`, thus enabling the validation of any observation value against its DSD.  
 
Dataflow definition
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

A :index:`dataflow` describes what a particular dataset is about, 
how often it is updated over time by its providing agency, under what conditions it will be provided etc.
A great deal of this metadata is expressed by references to other artefacts such as a data structure definition.
  
A :index:`DataFlowDefinition` is a class that describes a dataflow. A DataFlow  
has a unique identifier, a human-readable name and potentially a more detailed description. Both may be multi-lingual.
The dataflow's ID is used to query the dataset it describes. The dataflow also features a 
reference to the DSD which structures the datasets available under this
dataflow ID. In the frontpage example we used the dataflow ID 'une_rt_a'.

  