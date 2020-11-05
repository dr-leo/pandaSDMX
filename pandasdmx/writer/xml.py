"""SDMXML v2.1 writer."""
# Contents of this file are organized in the order:
#
# - Utility methods and global variables.
# - writer functions for pandasdmx.message classes, in the same order as message.py
# - writer functions for pandasdmx.model classes, in the same order as model.py

from itertools import chain
from typing import Iterable, cast

from lxml import etree
from lxml.builder import ElementMaker

import pandasdmx.urn
from pandasdmx import message, model
from pandasdmx.format.xml import NS, qname, tag_for_class
from pandasdmx.writer.base import BaseWriter

_element_maker = ElementMaker(nsmap={k: v for k, v in NS.items() if v is not None})

writer = BaseWriter("XML")


def Element(name, *args, **kwargs):
    """
    Create a new element.

    Args:
        name: (str): write your description
    """
    # Remove None
    kwargs = dict(filter(lambda kv: kv[1] is not None, kwargs.items()))

    return _element_maker(qname(name), *args, **kwargs)


def to_xml(obj, **kwargs):
    """Convert an SDMX *obj* to SDMX-ML.

    Parameters
    ----------
    kwargs
        Passed to :meth:`lxml.etree.to_string`, e.g. `pretty_print` =
        :obj:`True`.

    Raises
    ------
    NotImplementedError
        If writing specific objects to SDMX-ML has not been implemented in
        :mod:`sdmx`.
    """
    return etree.tostring(writer.recurse(obj), **kwargs)


def reference(obj, parent=None, tag=None, style="URN"):
    """Write a reference to `obj`."""
    tag = tag or tag_for_class(obj.__class__)

    elem = Element(tag)

    if style == "URN":
        ref = Element(":URN", obj.urn)
    elif style == "Ref":
        if isinstance(obj, model.MaintainableArtefact):
            ma = obj
        else:
            # TODO handle references to non-maintainable children of parent
            #      objects
            if not parent:
                for is_ in chain(
                    writer._message.concept_scheme.values(),
                    writer._message.category_scheme.values(),
                ):
                    if obj in is_:
                        parent = is_
                        break

            if not parent:
                raise NotImplementedError(
                    f"Cannot write reference to {repr(obj)} without parent"
                )

            ma = parent

        args = {
            "id": obj.id,
            "maintainableParentID": ma.id if parent else None,
            "maintainableParentVersion": ma.version if parent else None,
            "agencyID": getattr(ma.maintainer, "id", None),
            "version": ma.version,
            "package": model.PACKAGE[obj.__class__],
            "class": etree.QName(tag_for_class(obj.__class__)).localname,
        }

        ref = Element(":Ref", **args)
    else:  # pragma: no cover
        raise ValueError(style)

    elem.append(ref)
    return elem


# Writers for pandasdmx.message classes


@writer
def _dm(obj: message.DataMessage):
    """
    Convert datastore message. datastructure.

    Args:
        obj: (todo): write your description
        message: (str): write your description
        DataMessage: (str): write your description
    """
    elem = Element("mes:GenericData")

    header = writer.recurse(obj.header)
    elem.append(header)

    # Add DSD references to header
    for ds in obj.data:
        attrib = dict()
        dsd_ref = None

        if ds.structured_by:
            attrib["structureID"] = ds.structured_by.id

            # Reference by URN if possible, otherwise with a <Ref> tag
            style = "URN" if ds.structured_by.urn else "Ref"
            dsd_ref = reference(ds.structured_by, tag="com:Structure", style=style)
        if isinstance(obj.observation_dimension, model.DimensionComponent):
            attrib["dimensionAtObservation"] = obj.observation_dimension.id

        header.append(Element("mes:Structure", **attrib))
        header[-1].append(dsd_ref)

        elem.append(writer.recurse(ds))

    return elem


@writer
def _sm(obj: message.StructureMessage):
    """
    Convert an smtp message.

    Args:
        obj: (todo): write your description
        message: (str): write your description
        StructureMessage: (str): write your description
    """
    # Store a reference to the overal Message for writing references
    setattr(writer, "_message", obj)

    elem = Element("mes:Structure")

    # Empty header element
    elem.append(writer.recurse(obj.header))

    structures = Element("mes:Structures")
    elem.append(structures)

    for attr, tag in [
        # Order is important here to avoid forward references
        ("organisation_scheme", "OrganisationSchemes"),
        ("dataflow", "Dataflows"),
        ("category_scheme", "CategorySchemes"),
        ("categorisation", "Categorisations"),
        ("codelist", "Codelists"),
        ("concept_scheme", "Concepts"),
        ("structure", "DataStructures"),
        ("constraint", "Constraints"),
        ("provisionagreement", "ProvisionAgreements"),
    ]:
        if not len(getattr(obj, attr)):
            continue
        container = Element(f"str:{tag}")
        container.extend(writer.recurse(s) for s in getattr(obj, attr).values())
        structures.append(container)

    return elem


@writer
def _header(obj: message.Header):
    """
    Generate a header string.

    Args:
        obj: (todo): write your description
        message: (str): write your description
        Header: (dict): write your description
    """
    elem = Element("mes:Header")
    elem.append(Element("mes:Test", str(obj.test).lower()))
    if obj.id:
        elem.append(Element("mes:ID", obj.id))
    if obj.prepared:
        elem.append(Element("mes:Prepared", obj.prepared.isoformat()))
    if obj.sender:
        elem.append(writer.recurse(obj.sender, _tag="mes:Sender"))
    if obj.source:
        elem.extend(i11lstring(obj.source, "mes:Source"))
    if obj.receiver:
        elem.append(writer.recurse(obj.receiver, _tag="mes:Receiver"))
    return elem


# Writers for pandasdmx.model classes
# §3.2: Base structures


def i11lstring(obj, name):
    """InternationalString.

    Returns a list of elements with name `name`.
    """
    elems = []

    for locale, label in obj.localizations.items():
        child = Element(name, label)
        child.set(qname("xml", "lang"), locale)
        elems.append(child)

    return elems


@writer
def _a(obj: model.Annotation):
    """
    Convert an element to an xml string.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Annotation: (todo): write your description
    """
    elem = Element("com:Annotation")
    if obj.id:
        elem.attrib["id"] = obj.id
    if obj.type:
        elem.append(Element("com:AnnotationType", obj.type))
    elem.extend(i11lstring(obj.text, "com:AnnotationText"))
    return elem


def annotable(obj, **kwargs):
    """
    Annotate an annotation.

    Args:
        obj: (todo): write your description
    """
    cls = kwargs.pop("_tag", tag_for_class(obj.__class__))
    try:
        elem = Element(cls, **kwargs)
    except AttributeError:  # pragma: no cover
        print(repr(obj), cls, kwargs)
        raise

    if len(obj.annotations):
        e_anno = Element("com:Annotations")
        e_anno.extend(writer.recurse(a) for a in obj.annotations)
        elem.append(e_anno)

    return elem


def identifiable(obj, **kwargs):
    """
    Annotate an object.

    Args:
        obj: (todo): write your description
    """
    kwargs.setdefault("id", obj.id)
    try:
        kwargs.setdefault(
            "urn", obj.urn or pandasdmx.urn.make(obj, kwargs.pop("parent", None))
        )
    except (AttributeError, ValueError):
        pass
    return annotable(obj, **kwargs)


def nameable(obj, **kwargs):
    """
    Return the name of an object.

    Args:
        obj: (todo): write your description
    """
    elem = identifiable(obj, **kwargs)
    elem.extend(i11lstring(obj.name, "com:Name"))
    elem.extend(i11lstring(obj.description, "com:Description"))
    return elem


def maintainable(obj, **kwargs):
    """
    Returns the nameable object to be able to call.

    Args:
        obj: (todo): write your description
    """
    kwargs.setdefault("version", obj.version)
    kwargs.setdefault("isExternalReference", str(obj.is_external_reference).lower())
    kwargs.setdefault("isFinal", str(obj.is_final).lower())
    kwargs.setdefault("agencyID", getattr(obj.maintainer, "id", None))
    return nameable(obj, **kwargs)


# §3.5: Item Scheme


@writer
def _item(obj: model.Item, **kwargs):
    """
    Convert an item for the given a list.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Item: (todo): write your description
    """
    elem = nameable(obj, **kwargs)

    if obj.parent:
        # Reference to parent Item
        e_parent = Element("str:Parent")
        e_parent.append(Element(":Ref", id=obj.parent.id))
        elem.append(e_parent)

    return elem


@writer
def _is(obj: model.ItemScheme):
    """
    Returns true if obj is a list of obj.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        ItemScheme: (todo): write your description
    """
    elem = maintainable(obj)
    elem.extend(writer.recurse(i) for i in obj.items.values())
    return elem


# §3.6: Structure


@writer
def _facet(obj: model.Facet):
    """
    Return the facet by an object

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Facet: (todo): write your description
    """
    # TODO textType should be CamelCase
    return Element("str:TextFormat", textType=getattr(obj.value_type, "name", None))


@writer
def _rep(obj: model.Representation, tag, style="URN"):
    """
    Represents an element.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Representation: (todo): write your description
        tag: (str): write your description
        style: (str): write your description
    """
    elem = Element(f"str:{tag}")
    if obj.enumerated:
        elem.append(reference(obj.enumerated, tag="str:Enumeration", style=style))
    if obj.non_enumerated:
        elem.extend(writer.recurse(facet) for facet in obj.non_enumerated)
    return elem


# §4.4: Concept Scheme


@writer
def _concept(obj: model.Concept, **kwargs):
    """
    Convert a concept to a concept.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Concept: (todo): write your description
    """
    elem = _item(obj, **kwargs)

    if obj.core_representation:
        elem.append(writer.recurse(obj.core_representation, "CoreRepresentation"))

    return elem


# §3.3: Basic Inheritance


@writer
def _component(obj: model.Component):
    """
    Create a component.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Component: (todo): write your description
    """
    elem = identifiable(obj)
    if obj.concept_identity:
        elem.append(
            reference(obj.concept_identity, tag="str:ConceptIdentity", style="Ref",)
        )
    if obj.local_representation:
        elem.append(
            writer.recurse(obj.local_representation, "LocalRepresentation", style="Ref")
        )
    # DataAttribute only
    try:
        elem.append(writer.recurse(cast(model.DataAttribute, obj).related_to))
    except AttributeError:
        pass
    return elem


@writer
def _cl(obj: model.ComponentList):
    """
    Return a list of obj to model instances.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        ComponentList: (list): write your description
    """
    elem = identifiable(obj)
    elem.extend(writer.recurse(c) for c in obj.components)
    return elem


# §4.5: CategoryScheme


@writer
def _cat(obj: model.Categorisation):
    """
    Return a reference to an object

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Categorisation: (todo): write your description
    """
    elem = maintainable(obj)
    elem.extend(
        [
            reference(obj.artefact, tag="str:Source", style="Ref"),
            reference(obj.category, tag="str:Target", style="Ref"),
        ]
    )
    return elem


# §10.3: Constraints


@writer
def _ms(obj: model.MemberSelection):
    """
    Return a list of elementtree objects into a list.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        MemberSelection: (todo): write your description
    """
    elem = Element("com:KeyValue", id=obj.values_for.id)
    elem.extend(Element("com:Value", mv.value) for mv in obj.values)
    return elem


@writer
def _cr(obj: model.CubeRegion):
    """
    Generate the cront object.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        CubeRegion: (str): write your description
    """
    elem = Element("str:CubeRegion", include=str(obj.included).lower())
    elem.extend(writer.recurse(ms) for ms in obj.member.values())
    return elem


@writer
def _cc(obj: model.ContentConstraint):
    """
    Generate a list of objects.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        ContentConstraint: (todo): write your description
    """
    elem = maintainable(
        obj, type=obj.role.role.name.replace("allowable", "allowed").title()
    )

    # Constraint attachment
    for ca in obj.content:
        elem.append(Element("str:ConstraintAttachment"))
        elem[-1].append(reference(ca, style="Ref"))

    elem.extend(writer.recurse(dcr) for dcr in obj.data_content_region)
    return elem


# §5.2: Data Structure Definition


@writer
def _nsr(obj: model.NoSpecifiedRelationship):
    """
    Return an elementtree element.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        NoSpecifiedRelationship: (todo): write your description
    """
    elem = Element("str:AttributeRelationship")
    elem.append(Element("str:None"))
    return elem


@writer
def _pmr(obj: model.PrimaryMeasureRelationship):
    """
    Generate a list of objects.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        PrimaryMeasureRelationship: (todo): write your description
    """
    elem = Element("str:AttributeRelationship")
    elem.append(Element("str:PrimaryMeasure"))
    elem[-1].append(Element(":Ref", id="(not implemented)"))
    return elem


@writer
def _dr(obj: model.DimensionRelationship):
    """
    Generate a list of element objects.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        DimensionRelationship: (int): write your description
    """
    elem = Element("str:AttributeRelationship")
    for dim in obj.dimensions:
        elem.append(Element("str:Dimension"))
        elem[-1].append(Element(":Ref", id=dim.id))
    return elem


@writer
def _gr(obj: model.GroupRelationship):
    """
    Return group element group

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        GroupRelationship: (todo): write your description
    """
    elem = Element("str:AttributeRelationship")
    elem.append(Element("str:Group"))
    elem[-1].append(Element(":Ref", id=getattr(obj.group_key, "id", None)))
    return elem


@writer
def _gdd(obj: model.GroupDimensionDescriptor):
    """
    Return a list of obj for each element

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        GroupDimensionDescriptor: (todo): write your description
    """
    elem = identifiable(obj)
    for dim in obj.components:
        elem.append(Element("str:GroupDimension"))
        elem[-1].append(Element("str:DimensionReference"))
        elem[-1][0].append(Element(":Ref", id=dim.id))
    return elem


@writer
def _dsd(obj: model.DataStructureDefinition):
    """
    Convert dsdict objects into a list.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        DataStructureDefinition: (str): write your description
    """
    elem = maintainable(obj)
    elem.append(Element("str:DataStructureComponents"))

    # Write in a specific order
    elem[-1].append(writer.recurse(obj.dimensions))
    for group in obj.group_dimensions.values():
        elem[-1].append(writer.recurse(group))
    elem[-1].append(writer.recurse(obj.attributes))
    elem[-1].append(writer.recurse(obj.measures))

    return elem


@writer
def _dfd(obj: model.DataflowDefinition):
    """
    Convert a dataframe from a pandas dataframe objects into a pandas dataframe.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        DataflowDefinition: (todo): write your description
    """
    elem = maintainable(obj)
    elem.append(reference(obj.structure, tag="str:Structure", style="Ref"))
    return elem


# §5.4: Data Set


def _av(obj: Iterable[model.AttributeValue]):
    """
    Return an iterator over all the objects.

    Args:
        obj: (todo): write your description
        Iterable: (todo): write your description
        model: (todo): write your description
        AttributeValue: (todo): write your description
    """
    for av in obj:
        assert av.value_for
        yield Element("gen:Value", id=av.value_for.id, value=av.value)


@writer
def _sk(obj: model.SeriesKey):
    """
    Return a sklearn element.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        SeriesKey: (str): write your description
    """
    elem = []

    elem.append(Element("gen:SeriesKey"))
    elem[-1].extend(
        Element("gen:Value", id=kv.value_for.id, value=kv.value) for kv in obj
    )
    if len(obj.attrib):
        elem.append(Element("gen:Attributes"))
        elem[-1].extend(_av(obj.attrib.values()))

    return tuple(elem)


@writer
def _obs(obj: model.Observation):
    """
    Returns a list of a list.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        Observation: (dict): write your description
    """
    elem = Element("gen:Obs")

    assert obj.dimension and len(obj.dimension) == 1
    elem.append(Element("gen:ObsDimension", value=obj.dimension.values[0].value))
    elem.append(Element("gen:ObsValue", value=obj.value))

    if len(obj.attached_attribute):
        elem.append(Element("gen:Attributes"))
        elem[-1].extend(_av(obj.attached_attribute.values()))

    return elem


@writer
def _ds(obj: model.DataSet):
    """
    Returns a list of - element objects to a list of model objects.

    Args:
        obj: (todo): write your description
        model: (todo): write your description
        DataSet: (todo): write your description
    """
    if len(obj.group):
        raise NotImplementedError("to_xml() for DataSet with groups")

    attrib = dict()
    if obj.action:
        attrib["action"] = str(obj.action)
    if obj.structured_by:
        attrib["structureRef"] = obj.structured_by.id
    elem = Element("mes:DataSet", **attrib)

    for sk, observations in obj.series.items():
        elem.append(Element("gen:Series"))
        elem[-1].extend(writer.recurse(sk))
        elem[-1].extend(writer.recurse(obs) for obs in observations)

    return elem
