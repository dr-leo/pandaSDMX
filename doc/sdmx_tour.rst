.. _sdmx-tour:
 
A very short introduction to SDMX
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
a more efficient JSON-variant is being standardised by the 
`SDMX Technical Standards Working Group <https://github.com/sdmx-twg>`_. 
 
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
where all dimension values including time, if available, are stated for each observation, are called :index:`flat datasets`. These are not 
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
how often it is updated over time by its maintaining agency, under what conditions it will be provided etc.
The terminology is a bit confusing: You cannot actually
obtain a dataflow from an SDMX web service. Rather, you can request one or more dataflow definitions
describing a flow of data over time. The dataflow definition and the artefacts to which it refers give you
all the information you need to exploit the datasets you can request using the dataflow's ID. 
    
A :index:`DataFlowDefinition` is a class that describes a dataflow. A DataFlowDefinition  
has a unique identifier, a human-readable name and potentially a more detailed description. Both may be multi-lingual.
The dataflow's ID is used to query the dataset it describes. The dataflow also features a 
reference to the DSD which structures the datasets available under this
dataflow ID. For instance, in the frontpage example we used the dataflow ID 'une_rt_a'.
  
  
Constraints
:::::::::::::::::
  
There are two types of constraints:
  
A :index:`content-constraint` is a mechanism to express the fact
that datasets of a given dataflow only comprise columns for a subset of values from
the code-lists representing dimension values. For example,
the datastructure definition for a dataflow on exchange rates
references tha codelist of all country codes in the world, whereas
the datasets provided under this dataflow only covers the ten largest currencies. These can be 
enumerated by a content-constraint attached to the dataflow definition.
Content-constraints can be used to validate dimension names and values (a.k.a. keys)
when requesting datasets selecting columns of interest.

An :index:`attachment-constraint` describes to which parts of a dataset (column/series,
group of series, observation, the entire dataset) certain attributes may be attached. Attachment-constraints are not
supported by pandaSDMX as this feature is needed only for 
dataset generation. However, pandaSDMX does support attributes in the information model
and when exporting datasets to pandas.

  
Category schemes and categorisations
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

Categories serve to classify or categorise things like dataflows, e.g., by subject matter. 
Multiple categories may belong to a container called :index:`CategorySchemes`. 

A :index:`Categorisation` links the thing to be
categorised, e.g., a DataFlowDefinition, to a :index:`Category`. 

Class hierarchy
:::::::::::::::::

The SDMX information model defines a number of base classes from which concrete classes
such as :index:`DataFlowDefinition` or :index:`DataStructureDefinition` inherit.
E.g., DataFlowDefinition inherits from :index:`MaintainableArtefact` attributes indicating the maintaining
agency. MaintainableArtefact inherits from :index:`VersionableArtefact`, which, in turn, inherits from
:index:`IdentifiableArtefact` which inherits from :index:`AnnotableArtefact` and so forth. Hence, DataStructureDefinition may have a unique
ID, a version, a natural language name in multiple languages, a description, and annotations. pandaSDMX takes advantage from
this class hierarchy.
    
Implementations of the information model
---------------------------------------------------------------      
      
Background
:::::::::::
      
There are two implementations of the information model:

* SDMXML is XML-based. It is fully standardised and covers the
  complete information model. However, it is a bit heavy-weight and data providers
  are gradually shifting to the JSON flavor currently in the works. 
* `SDMXJSON <https://github.com/sdmx-twg/sdmx-json>`_: 
  This recent JSON-based implementation is more lightweight and efficient.
  While standardisation is in an advanced stage, structure-messages are not yet covered. Data messages work well
  hough, and pandaSDMX supports them as from v0.5.
          
SDMXML
:::::::::
      
The SDMX standard defines an XML-based implementation of the information model called :index:`SDMXML`. 
An SDMXML document contains exactly one SDMX :index:`Message`. There are several types of Message such as
:index:`GenericDataMessage` to represent a :index:`DataSet` in generic form, i.e. containing
all the information required to interpret it. Hence, datasets in generic representation may be used without
knowing the related :index:`DataStructureDefinition`. The downside is that generic dataset messages are
much larger than their sister format :index:`StructureSpecificDataSet`. pandaSDMX as of v0.2 only supports generic
dataset messages. 
  
Another important SDMXML message type is :index:`StructureMessage` 
which may contain artefacts such as DataStructureDefinitions, codelists,
conceptschemes, categoryschemes and so forth.
  
SDMXML provides that each message contains a :index:`Header` containing some metadata about the message.
Finally, SDMXML messages may contain a :index:`Footer` element. It provides information on any errors
that have occurred on the server side, e.g., if the requested dataset exceeds the size limit, or the server needs
some time to make it available under a given link. 

The test suite comes with a number of small SDMXML demo files. View them in your favorite 
XML editor to get a deeper understanding of the structure and content of various message types. 

SDMX services provide XML schemas to validate a particular SDMXML file. However, pandaSDMX does not 
yet support validation.
        
SDMXJSON
::::::::::
        
`SDMXJSON <https://github.com/sdmx-twg/sdmx-json>`_ represents SDMX datasets and related metadata as
JSON files provided by RESTful web services. Early adopters of this format are OECD, ECB and IMF. As of v0.5, pandaSDMX
supports the OECD's REST interface for SDMXJSON. However, note that
structural metadata is not yet fully standardised. Hence, it is impossible at
this stage to download dataflow definitions, codelists etc. from OECD. 
 
        
SDMX web services
--------------------------------
        
The SDMX standard defines both a REST and a SOAP web service API. As of v0.5, pandaSDMX only supports the REST API.        

The URL specifies the type, providing agency, and ID of the requested SDMX resource (dataflow, categoryscheme, data etc.).
The query part of the URL (after the '?') may be used to give optional query parameters. For instance, when
requesting data, the scope of the dataset may be narrowed down by specifying a key to select only matching 
columns (e.g. on a particular country). The dimension names and values
used to select the rows can be validated by checking if they are
contained in the relevant codelists referenced by the
datastructure definition (see above), and any content-constraint attached
to the dataflow definition for the queried dataset. 
Moreover, rows may be chosen by specifying a startperiod and endperiod for the time series. In addition,
the query part may set a :index:`references` parameter to instruct the
SDMX server to return a number of other artefacts along with the resource actually requested.
For example, a DataStructureDefinition contains references to codelists and conceptschemes (see above). If the
'references' parameter is set to 'all', these will be returned in the same StructureMessage.
The next chapter contains some examples to demonstrate this mechanism. Further details can be found in the
SDMX User Guide, and the Web Service Guidelines.

Further reading
------------------------------------

* The `SDMX standards and guidelines <http://sdmx.org/?cat=5>`_ are the 
  authoritative resource. This page is a must for anyone eager to dive deeper into
  SDMX. Start with the User Guide and the Information Model (Part 2 of the standard).
  The Web Services Guidelines contain instructive examples for typical queries.
* `Eurostat SDMX page <http://ec.europa.eu/eurostat/data/sdmx-data-metadata-exchange>`_
* `European Central Bank SDMX page <https://sdw-wsrest.ecb.europa.eu/>`_
  It links to a range of study guides and helpful video tutorials.
* `SDMXSource <http://www.sdmxsource.org/>`_:
  - Java, .NET and ActionScript implementations of SDMX software, in part open source
    
 
       
