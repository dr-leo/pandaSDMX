The SDMX Information Model
==========================

The module :mod:`pandasdmx.model` implements the SDMX Information Model
(SDMX-IM). The `SDMX website <https://sdmx.org/?page_id=5008>`_ hosts the
`full specification of the IM <https://sdmx.org/wp-content/uploads/SDMX_2-1-1_SECTION_2_InformationModel_201108.pdf>`_ (PDF format); this page gives a
brief explanation of the SDMX-IM classes as they appear in pandaSDMX.

.. contents::
   :local:
   :backlinks: none

Abstract classes and data types
-------------------------------

.. currentmodule:: pandasdmx.model

Many classes inherit from one of the following classes. For instance, a :class:`Code` is a ``NameableArtefact``; [1]_ this means it has `name` and `description` attributes. It also has the `id`, `URI`, and `URN` attributes of an ``IndentifiableArtefact``. The API reference for :mod:`pandasdmx.model` describes the parent classes for each class.

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
