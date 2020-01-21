Overview of SDMX
****************

Extensive information on SDMX, including learning material, is available in multiple places on the Internet.
:ref:`As stated<not-the-standard>`, the documentation you are reading does not duplicate this information
This overview page provides notes to help explain *how* :mod:`pandaSDMX` implements the standards, in order to help you make use of it.

.. _resources:

Other resources
===============

If you want to learn about SDMX *in general*, please make use of the following resources—and offer feedback to help improve them!

- Wikipedia's `SDMX page <https://en.wikipedia.org/wiki/SDMX>`_ page gives a simple summary in 6 languages.
- Eurostat's `SDMX ‘InfoSpace’ <https://ec.europa.eu/eurostat/web/sdmx-infospace/welcome>`_ contains many guides and tutorials, from beginner to advanced levels.
- The SDMX website includes both `the authoritative standards <https://sdmx.org/?page_id=5008>`_ and `many detailed guidelines <https://sdmx.org/?page_id=4345>`_ for their use.
  In particular, see `Section 2 — Information Model <http://sdmx.org/wp-content/uploads/SDMX_2-1-1_SECTION_2_InformationModel_201108.pdf>`_.

- The GitHub organization of the `SDMX Technical Standards Working Group <https://github.com/sdmx-twg>`_ hosts other standards information, such as the `Section 7 — REST web service <https://github.com/sdmx-twg/sdmx-rest>`_ standard.
- The European Central Bank `SDMX REST service help pages <https://sdw-wsrest.ecb.europa.eu/help/>`_ give many examples.
- `SDMXSource <http://www.sdmxsource.org>`_ provides reference implementations of SDMX in Java, .NET and ActionScript.

.. contents::
   :backlinks: none


Standards versions
==================

:mod:`pandaSDMX` supports the SDMX version 2.1, the latest.
SDMX 2.0 and 1.0 were released previously.

Some agencies offer :ref:`web-service` that give users the option to retrieve data in SDMX 2.1 *or* 2.0 formats.
Others *only* provide SDMX 2.0-formatted data; these services cannot be used with :mod:`pandaSDMX`.


.. _im:

The SDMX Information Model (IM)
===============================

At its core, SDMX defines an :index:`information model` consisting of a set of :index:`classes`, their logical relations, and semantics.
There are classes defining things like data sets, metadata sets, data and metadata structures, processes, organisations and their specific roles to name but a few.
The information model is agnostic as to its implementation.
The SDMX standard provides an XML-based implementation (see below).
And a more efficient JSON-variant called SDMXJSON is being standardised by the
`SDMX Technical Standards Working Group <https://github.com/sdmx-twg>`_. PandaSDMX supports both formats.

The following sections briefly introduces some key elements of the information model.

Data sets
---------

a :index:`data set` can broadly be described as a
container of ordered :index:`observations` and :index:`attributes` attached to them. Observations (e.g. the annual unemployment rate) are classified
by :index:`dimensions` such as country, age, sex, and time period. Attributes may further describe an individual observation or
a set of observations. Typical uses for attributes are the level of confidentiality, or data quality.
Observations may be clustered into :index:`series`, in particular, time series. The data set
must explicitly specify the :index:`dimension at observation` such as 'time', 'time_period' or anything else.
If a data set consists of series whose
dimension at observation is neither time nor time period, the data set is called :index:`cross-sectional`.
A data set that is not grouped into series, i.e.
where all dimension values including time, if available, are stated for each observation, are called :index:`flat data sets`. These are hardly
memory-efficient, but benefit from a very simple representation.

An attribute may be attached to a series to express
the fact that it applies to all contained observations. This increases
efficiency and adds meaning. Subsets of series within a data set may be clustered into :index:`groups`.
A group is
defined by specifying one or more dimension values, but not all: At least the dimension at observation and one other
dimension must remain free (or wild-carded). Otherwise, the group would in fact be either a single observation or a series.
The main purpose of :index:`group` is to
serve as a convenient attachment point for attributes. Hence, a given attribute may be attached to all series
within the group at once. Attributes may finally be attached to the entire data set, i.e. to all series/observations therein.

Structural metadata: data structure definition, concept scheme, and code list
-----------------------------------------------------------------------------

In the above section on data sets, we have carelessly used structural terms such as dimension, dimension value and
attachment of attributes. This is because it is almost impossible to talk about data sets without talking about their structure. The information model
provides a number of classes to describe the structure of data sets without talking about data. The container class for this is called
:index:`DataStructureDefinition` (in short: :abbr:`DSD`). It contains a list of dimensions and for each dimension a reference to exactly one
:index:`concept` describing its meaning. A concept describes the set of permissible dimension values. This can
be done in various ways depending on the intended data type. Finite value sets (such as country codes, currencies, a data quality classification etc.) are
described by reference to :index:`code lists`. Infinite value sets are described by :index:`facets` which is simply a
way to express that a dimension may have int, float or time-stamp values, to name but a few. A set of concepts referred to in the
dimension descriptors of a data structure definition is called :index:`concept scheme`.

The set of allowed observation values such as the unemployment rate measured in per cent is
defined by a special dimension called :index:`MeasureDimension`.

Dataflow definition
-------------------

A :index:`dataflow` describes how a particular data set is structured (by referring to a DSD),
how often it is updated over time by its maintaining agency, under what conditions it will be provided etc.
The terminology is a bit confusing: You cannot actually
obtain a dataflow from an SDMX web service. Rather, you can request one or more dataflow definitions
describing how datasets under this dataflow are structured, which codes may be used to
query for desired columns etc. The dataflow definition and the artefacts to which it refers give you
all the information you need to exploit the data sets you can request using the dataflow's ID.

A :index:`DataFlowDefinition` is a class that describes a dataflow. A DataFlowDefinition
has a unique identifier, a human-readable name and potentially a more detailed description. Both may be multi-lingual.
The dataflow's ID is used to query the data set it describes. The dataflow also features a
reference to the DSD which structures the data sets available under this
dataflow ID. For instance, in the frontpage example we used the dataflow ID 'une_rt_a'.


Constraints
-----------

Constraints are a mechanism to specify a subset of
keys from the set of possible combinations of keys
available in the referenced code lists for which there is actually data. For example,
a constraint may reflect the fact that in a certain country
there are no lakes or hospitals, and hence no data about water quality or
hospitalization.

There are two types of constraints:

A :index:`content-constraint` is a mechanism to express the fact
that data sets of a given dataflow only comprise columns for a subset of values from
the code-lists representing dimension values. For example,
the datastructure definition for a dataflow on exchange rates
references the code list of all country codes in the world, whereas
the data sets provided under this dataflow only covers the ten largest currencies. These can be
enumerated by a content-constraint attached to the dataflow definition or DSD.
Content-constraints can be used to validate dimension names and values (a.k.a. keys)
when requesting data sets selecting columns of interest. pandaSDMX supports content
constraints and provides convenient methods to validate keys, compute
the constrained code lists etc.


An :index:`attachment-constraint` describes to which parts of a data set (column/series,
group of series, observation, the entire data set) certain attributes may be attached. Attachment-constraints are not
supported by pandaSDMX as this feature is needed only for
data set generation. However, pandaSDMX does support attributes in the information model
and when exporting data sets to pandas.

Category schemes and categorisations
------------------------------------

Categories serve to classify or categorise things like dataflows, e.g., by subject matter.
Multiple categories may belong to a container called :index:`CategorySchemes`.

A :index:`Categorisation` links the thing to be
categorised, e.g., a DataFlowDefinition, to a :index:`Category`.

Class hierarchy
---------------

The SDMX information model defines a number of abstract base classes from which subclasses
such as :index:`DataFlowDefinition` or :index:`DataStructureDefinition` are derived.
E.g., DataFlowDefinition inherits from :index:`MaintainableArtefact` attributes indicating the maintaining
agency. MaintainableArtefact inherits from :index:`VersionableArtefact`, which, in turn, inherits from
:index:`IdentifiableArtefact` which inherits from :index:`AnnotableArtefact` and so forth. Hence, DataStructureDefinition may have a unique
ID, a version, a natural language name in multiple languages, a description, and annotations. pandaSDMX takes full advantage from
this class hierarchy.


The SDMX Information Model (IM) 2
=================================

:mod:`pandasdmx.model` implements the SDMX Information Model (SDMX-IM).
The `SDMX website <https://sdmx.org/?page_id=5008>`_ hosts the `full specification of the IM <sdmx-im>`_ (PDF format); this page gives a
brief overview of the SDMX-IM classes as they appear in :mod:`pandaSDMX`.

.. _sdmx-im: https://sdmx.org/wp-content/uploads/SDMX_2-1-1_SECTION_2_InformationModel_201108.pdf

Abstract classes and data types
-------------------------------

.. currentmodule:: pandasdmx.model

Many classes inherit from one of the following classes.
For example, a :class:`Code` is a ``NameableArtefact``; [1]_ this means it has `name` and `description` attributes. Because every ``NameableArtefact`` is an ``IdentifiableArtefact``, it also has `id`, `URI`, and `URN` attributes.
The API reference for :mod:`pandasdmx.model` shows the parent classes for each class.

- An :class:`IdentifiableArtefact` has an :attr:`id <IdentifiableArtefact.id>`,
  :attr:`URI <IdentifiableArtefact.uri>`, and
  :attr:`URN <IdentifiableArtefact.urn>`.

  - The ``id`` uniquely identifies the object against others of the same type in
    a SDMX message.
  - The URI and URN are *globally* unique. See `Wikipedia <https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#URLs_and_URNs>`_ for a
    discussion of the differences between the two.

- A :class:`NameableArtefact` has a :attr:`name <NameableArtefact.name>` and
  :attr:`description <NameableArtefact.description>`. It is identifiable; this
  means that it *also* has the `id`, `uri`, and `urn` attributes of a
  ``NameableArtefact``.
- A :class:`VersionableArtefact` has a
  :attr:`version <VersionableArtefact.version>` number and may be valid between
  certain times (:attr:`valid_from <VersionableArtefact.valid_from>`,
  :attr:`valid_to <VersionableArtefact.valid_to>`). It is nameable *and*
  identifiable.
- A :class:`MaintainableArtefact` is under the authority of a particular
  :attr:`maintainer <MaintainableArtefact.maintainer>`. In an SDMX message,
  a maintainable object might not be given in full; only as a reference (with
  :attr:`is_external_reference <MaintainableArtefact.is_external_reference>`
  set to True). If so, it might have a :attr:`structure_url
  <MaintainableArtefact.structure_url>`, where the maintainer provides more
  information about the object. It is versionable, nameable, and identifiable.

Because SDMX is used worldwide, an :class:`InternationalString` type is used in
the IM—for instance, the `name` of a Nameable object is an
``InternationalString``, with zero or more :attr:`localizations <InternationalString.localizations>` in different locales.

.. [1] Indirectly, through :class:`Item`.

Data
----

- The base :class:`DataSet` class is an unordered collection of
  :class:`Observation`. Each `Observation` is a single datum.

- :class:`Key`, :class:`SeriesKey`, :class:`GroupKey`.

Metadata: attributes
--------------------

- :class:`AttributeValue`.
- :class:`DataAttribute`.


Items and schemes
-----------------

- :class:`Item`.
- :class:`ItemScheme`.
- :class:`CategoryScheme`, :class:`ConceptScheme`, :class:`Codelist`.

Data structure and flow
-----------------------

- :class:`Dimension`, :class:`DimensionDescriptor`.
- :class:`AttributeDescriptor`.
- :class:`DataStructureDefinition`.
- :class:`DataflowDefinition`.


.. _formats:

Formats
=======

The :ref:`IM <im>` provides terms and concepts for data and metadata, but does not specify *how that (meta)data is stored or represented*.
The SDMX standards include multiple ways to store data, in the following formats:

SDMX-ML
    Based on eXtensible Markup Language (XML).
    SDMX-ML provides a *complete* specification: it can represent every class and property in the IM.

    Reference: https://sdmx.org/?page_id=5008

    - An SDMX-ML document contains exactly one Message.
      See :mod:`pandaSDMX.message` for the different types of Messages and their component parts.
    - See :mod:`.reader.sdmxml`.

SDMX-JSON
    Based on JavaScript Object Notation (JSON).
    The SDMX-JSON format is only defined for data, not metadata.

    Reference: https://github.com/sdmx-twg/sdmx-json

    - See :mod:`.reader.sdmxjson`.

    .. versionadded:: 0.5

       Support for SDMX-JSON.

SDMX-CSV
    Based on Comma-Separated Value (CSV).
    Like SDMX-JSON, the SDMX-CSV format are only defined for data, not metadata.

    Reference: https://github.com/sdmx-twg/sdmx-csv

    pandaSDMX **does not** currently support SDMX-CSV.

pandaSDMX:

- reads all kinds of SDMX-ML and SDMX-JSON messages.
- contains, in the `tests/data/ <https://github.com/dr-leo/pandaSDMX/tree/master/tests/data>`_ source directory, specimens of messages in both data formats.
  These are used by the test suite to check that the code functions as intended, but can also be viewed to understand the data formats.

SDMX-ML
-------

There are several types of Message such as
:index:`GenericDataMessage` to represent a :index:`data set` in generic form, i.e. containing
all the information required to interpret it. Hence, data sets in generic representation may be used without
knowing the related :index:`DataStructureDefinition`. The downside is that generic data set messages are
much larger than their sister format :index:`StructureSpecificdata set`. pandaSDMX has always supported generic
data set messages.

The term 'structure-specific dataset' reflects the fact that in order to interpret such
dataset, one needs to know the datastructure definition (DSD). Otherwise, it would be impossible
to distinguish dimension values from attributes etc. Hence, when downloading a structure-specific
dataset, pandaSDMX will download the DSD on the fly or retrieves it from a local cash.

Another important SDMXML message type is :index:`StructureMessage`
which may contain artefacts such as DataStructureDefinitions, code lists,
conceptschemes, categoryschemes and so forth.

SDMXML provides that each message contains a :index:`Header` containing some metadata about the message.
Finally, SDMXML messages may contain a :index:`Footer` element. It provides information on any errors
that have occurred on the server side, e.g., if the requested data set exceeds the size limit, or the server needs
some time to make it available under a given link.

SDMX services provide XML schemas to validate a particular SDMXML file. However, pandaSDMX does not
yet support validation.


.. _web-service:

Web services
============

The SDMX standard defines both `REST <https://en.wikipedia.org/wiki/Representational_state_transfer>`_ and `SOAP <https://en.wikipedia.org/wiki/SOAP>`_ web service APIs.
:mod:`pandaSDMX` only supports the SDMX RESTful web services API.

Reference: https://github.com/sdmx-twg/sdmx-rest/tree/master/v2_1/ws/rest/docs

To use a RESTful web service, a *client* (like pandaSDMX) makes HTTP queries to particular URLs, sometimes with HTTP headers.
Both the Eurostat and ECB :ref:`resources linked above <resources>` provide detailed descriptions of these URLs and headers, and how to use these to control the data or metadata returned for a query.

:class:`~pandasdmx.api.Request` and its :meth:`~.Request.get` construct valid URLs by automatically:

- fetching metadata need to validate a query, and
- handling variations in supported features and accepted URL parts and parameters across different :doc:`data sources <sources>`.
