"""SDMXML v2.1 reader."""
# Contents of this file are organized in the order:
#
# - Utility methods and global variables.
# - Reference and Reader classes.
# - Parser functions for sdmx.message classes, in the same order as message.py
# - Parser functions for sdmx.model classes, in the same order as model.py

import logging
import re
from collections import ChainMap, defaultdict
from copy import copy
from itertools import chain, count, product
from sys import maxsize
from typing import Any, Dict, Iterable, Mapping, Optional, Type, Union, cast

from dateutil.parser import isoparse
from lxml import etree
from lxml.etree import QName

import pandasdmx.urn
from pandasdmx import message, model
from pandasdmx.exceptions import XMLParseError  # noqa: F401
from pandasdmx.format.xml import CONTENT_TYPES, class_for_tag, qname
from pandasdmx.reader.base import BaseReader

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


PARSE = {}

SKIP = (
    "com:Annotations com:Footer footer:Message "
    # Key and observation values
    "gen:ObsDimension gen:ObsValue gen:Value "
    # Tags that are bare containers for other XML elements
    "str:Categorisations str:CategorySchemes str:Codelists str:Concepts "
    "str:ConstraintAttachment str:Constraints str:Dataflows "
    "str:DataStructureComponents str:DataStructures str:None str:OrganisationSchemes "
    "str:ProvisionAgreements str:StructureSets "
    # Contents of references
    ":Ref :URN"
)

TO_SNAKE_RE = re.compile("([A-Z]+)")


def add_localizations(target: model.InternationalString, values: list) -> None:
    """Add localized strings from *values* to *target*."""
    target.localizations.update({locale: label for locale, label in values})


def matching_class(cls):
    """Filter condition; see :meth:`.get_single` and :meth:`.pop_all`."""
    return lambda item: isinstance(item, type) and issubclass(item, cls)


def setdefault_attrib(target, elem, *names):
    try:
        for name in names:
            try:
                target.setdefault(to_snake(name), elem.attrib[name])
            except KeyError:
                pass
    except AttributeError:
        pass


def to_snake(value):
    """Convert *value* from lowerCamelCase to snake_case."""
    return TO_SNAKE_RE.sub(r"_\1", value).lower()


def start(*args, only=True):
    """Decorator for a function that parses "start" events for XML elements."""

    def decorator(func):
        for tag in to_tags(*args):
            PARSE[tag, "start"] = func
            if only:
                PARSE[tag, "end"] = None
        return func

    return decorator


def end(*args, only=True):
    """Decorator for a function that parses "end" events for XML elements."""

    def decorator(func):
        for tag in to_tags(*args):
            PARSE[tag, "end"] = func
            if only:
                PARSE[tag, "start"] = None
        return func

    return decorator


def to_tags(*args):
    return chain(*[[qname(tag) for tag in arg.split()] for arg in args])


PARSE.update({k: None for k in product(to_tags(SKIP), ["start", "end"])})


class NotReference(Exception):
    pass


_NO_AGENCY = model.Agency()


class Reference:
    """Temporary class for references.

    - `cls`, `id`, `version`, and `agency_id` are always for a MaintainableArtefact.
    - If the reference target is a MaintainableArtefact (`maintainable` is True),
      `target_cls` and `target_id` are identical to `cls` and `id`, respectively.
    - If the target is not maintainable, `target_cls` and `target_id` describe it.

    `cls_hint` is an optional hint for when the object is instantiated, i.e. a more
    specific override for `cls`/`target_cls`.
    """

    def __init__(self, elem, cls_hint=None):
        parent_tag = elem.tag

        try:
            # Use the first child
            elem = elem[0]
        except IndexError:
            raise NotReference

        # Extract information from the XML element
        if elem.tag == "Ref":
            # Element attributes give target_id, id, and version
            target_id = elem.attrib["id"]
            agency_id = elem.attrib.get("agencyID", None)
            id = elem.attrib.get("maintainableParentID", target_id)
            version = elem.attrib.get(
                "maintainableParentVersion", None
            ) or elem.attrib.get("version", None)

            # Attributes of the element itself, if any
            args = (elem.attrib.get("class", None), elem.attrib.get("package", None))
        elif elem.tag == "URN":
            match = pandasdmx.urn.match(elem.text)

            # If the URN doesn't specify an item ID, it is probably a reference to a
            # MaintainableArtefact, so target_id and id are the same
            target_id = match["item_id"] or match["id"]

            agency_id = match["agency"]
            id = match["id"]
            version = match["version"]

            args = (match["class"], match["package"])
        else:
            raise NotReference

        # Find the target class
        target_cls = model.get_class(*args)

        if target_cls is None:
            # Try the parent tag name
            target_cls = class_for_tag(parent_tag)

        if cls_hint and (target_cls is None or issubclass(cls_hint, target_cls)):
            # Hinted class is more specific than target_cls, or failed to find a target
            # class above
            target_cls = cls_hint

        self.maintainable = issubclass(target_cls, model.MaintainableArtefact)

        if self.maintainable:
            # MaintainableArtefact is the same as the target
            cls, id = target_cls, target_id
        else:
            # Get the class for the parent MaintainableArtefact
            cls = model.parent_class(target_cls)

        # Store
        self.cls = cls
        self.agency = model.Agency(id=agency_id) if agency_id else _NO_AGENCY
        self.id = id
        self.version = version
        self.target_cls = target_cls
        self.target_id = target_id

    def __str__(self):  # pragma: no cover
        return (
            f"{self.cls.__name__}={self.agency.id}:{self.id}({self.version}) → "
            f"{self.target_cls.__name__}={self.target_id}"
        )


class Reader(BaseReader):
    content_types = CONTENT_TYPES
    suffixes = [".xml"]

    # One-way counter for use in stacks
    _count = None

    def __init__(self):
        # Initialize counter
        self._count = count()

    @classmethod
    def detect(cls, content):
        return content.startswith(b"<")

    def read_message(
        self, source, dsd: model.DataStructureDefinition = None
    ) -> message.Message:
        # Initialize stacks
        self.stack: Dict[Union[Type, str], Dict[Union[str, int], Any]] = defaultdict(
            dict
        )

        # Elements to ignore when parsing finishes
        self.ignore = set()

        # If calling code provided a DSD, add it to a stack, and let it be ignored when
        # parsing finishes
        self.push(dsd)
        self.ignore.add(id(dsd))

        try:
            # Use the etree event-driven parser
            for event, element in etree.iterparse(source, events=("start", "end")):
                try:
                    # Retrieve the parsing function for this element & event
                    func = PARSE[element.tag, event]
                except KeyError:  # pragma: no cover
                    # Don't know what to do for this (element, event)
                    raise NotImplementedError(element.tag, event) from None

                try:
                    # Parse the element
                    result = func(self, element)
                except TypeError:
                    if func is None:  # Explicitly no parser for this (element, event)
                        continue  # Skip
                    else:  # pragma: no cover
                        raise
                else:
                    # Store the result
                    self.push(result)

                    if event == "end":
                        element.clear()  # Free memory

        except Exception as exc:
            # Parsing failed; display some diagnostic information
            self._dump()
            print(etree.tostring(element, pretty_print=True).decode())
            raise XMLParseError from exc

        # Parsing complete; count uncollected items from the stacks, which represent
        # parsing errors

        # Remove some internal items
        self.pop_single("SS without DSD")
        self.pop_single("DataSetClass")

        # Count only non-ignored items
        uncollected = -1
        for key, objects in self.stack.items():
            uncollected += sum(
                [1 if id(o) not in self.ignore else 0 for o in objects.values()]
            )

        if uncollected > 0:  # pragma: no cover
            self._dump()
            raise RuntimeError(f"{uncollected} uncollected items")

        return cast(message.Message, self.get_single(message.Message, subclass=True))

    def _clean(self):  # pragma: no cover
        """Remove empty stacks."""
        for key in list(self.stack.keys()):
            if len(self.stack[key]) == 0:
                self.stack.pop(key)

    def _dump(self):  # pragma: no cover
        """Print the stacks, for debugging."""
        self._clean()
        print("\n\n")
        for key, values in self.stack.items():
            print(f"--- {key} ---", values, sep="\n", end="\n\n")

    def push(self, stack_or_obj, obj=None):
        """Push an object onto a stack."""
        if stack_or_obj is None:
            return
        elif obj is None:
            # Add the object to a stack based on its class
            obj = stack_or_obj
            s = stack_or_obj.__class__
        elif isinstance(stack_or_obj, str):
            # Stack with a string name
            s = stack_or_obj
        else:
            # Element; use its local name
            s = QName(stack_or_obj).localname

        # Get the ID for the element in the stack: its .id attribute, if any, else a
        # unique number
        id = getattr(obj, "id", next(self._count)) or next(self._count)

        if id in self.stack[s]:
            # Avoid a collision for two distinct objects with the same ID, e.g. with
            # different maintainers (ECB:AGENCIES vs. SDMX:AGENCIES). Re-insert with
            # numerical keys. This means the objects cannot be retrieved by their ID,
            # but the code does not rely on this.
            self.stack[s][next(self._count)] = self.stack[s].pop(id)
            id = next(self._count)

        self.stack[s][id] = obj

    def stash(self, *stacks):
        """Temporarily hide all objects in the given `stacks`."""
        self.push("_stash", {s: self.stack.pop(s, dict()) for s in stacks})

    def unstash(self):
        """Restore the objects hidden by the last :meth:`stash` call to their stacks.

        Calls to :meth:`.stash` and :meth:`.unstash` should be matched 1-to-1; if the
        latter outnumber the former, this will raise :class:`.KeyError`.
        """
        for s, values in self.pop_single("_stash").items():
            self.stack[s].update(values)

    def get_single(
        self, cls_or_name: Union[Type, str], id: str = None, subclass: bool = False
    ) -> Optional[Any]:
        """Return a reference to an object while leaving it in its stack.

        Always returns 1 object. Returns :obj:`None` if no matching object exists, or if
        2 or more objects meet the conditions.

        If `id` is given, only return an IdentifiableArtefact with the matching ID.

        If `cls_or_name` is a class and `subclass` is :obj:`True`; check all objects in
        the stack `cls_or_name` *or any stack for a subclass of this class*.
        """
        if subclass:
            keys: Iterable[Union[Type, str]] = filter(
                matching_class(cls_or_name), self.stack.keys()
            )
            results: Mapping = ChainMap(*[self.stack[k] for k in keys])
        else:
            results = self.stack.get(cls_or_name, dict())

        if id:
            return results.get(id)
        elif len(results) != 1:
            # 0 or ≥2 results
            return None
        else:
            return next(iter(results.values()))

    def pop_all(self, cls_or_name: Union[Type, str], subclass=False) -> Iterable:
        """Pop all objects from stack *cls_or_name* and return.

        If `cls_or_name` is a class and `subclass` is :obj:`True`; return all objects in
        the stack `cls_or_name` *or any stack for a subclass of this class*.
        """
        if subclass:
            keys: Iterable[Union[Type, str]] = list(
                filter(matching_class(cls_or_name), self.stack.keys())
            )
            result: Iterable = chain(*[self.stack.pop(k).values() for k in keys])
        else:
            result = self.stack.pop(cls_or_name, dict()).values()

        return list(result)

    def pop_single(self, cls_or_name: Union[Type, str]):
        """Pop a single object from the stack for `cls_or_name` and return."""
        try:
            return self.stack[cls_or_name].popitem()[1]
        except KeyError:
            return None

    def peek(self, cls_or_name: Union[Type, str]):
        """Get the object at the top of stack `cls_or_name` without removing it."""
        try:
            key, value = self.stack[cls_or_name].popitem()
            self.stack[cls_or_name][key] = value
            return value
        except KeyError:  # pragma: no cover
            return None

    def pop_resolved_ref(self, cls_or_name: Union[Type, str]):
        """Pop a reference to `cls_or_name` and resolve it."""
        return self.resolve(self.pop_single(cls_or_name))

    def resolve(self, ref):
        """Resolve the Reference instance `ref`, returning the referred object."""
        if not isinstance(ref, Reference):
            # None, already resolved, or not a Reference
            return ref

        # Try to get the target directly
        target = self.get_single(ref.target_cls, ref.target_id, subclass=True)

        if target:
            return target

        # MaintainableArtefact with is_external_reference=True; either a new object, or
        # reference to an existing object
        target_or_parent = self.maintainable(
            ref.cls, None, id=ref.id, maintainer=ref.agency, version=ref.version
        )

        if ref.maintainable:
            # `target_or_parent` is the target
            return target_or_parent

        # At this point, trying to resolve a reference to a child object of a parent
        # MaintainableArtefact; `target_or_parent` is the parent
        parent = target_or_parent

        if parent.is_external_reference:
            # Create the child
            return parent.setdefault(id=ref.target_id)
        else:
            try:
                # Access the child. Mismatch here will raise KeyError
                return parent[ref.target_id]
            except KeyError:
                if isinstance(parent, model.ItemScheme):
                    return parent.get_hierarchical(ref.target_id)
                raise

    def annotable(self, cls, elem, **kwargs):
        """Create a AnnotableArtefact of `cls` from `elem` and `kwargs`.

        Collects all parsed <com:Annotation>.
        """
        if elem is not None:
            kwargs.setdefault("annotations", [])
            kwargs["annotations"].extend(self.pop_all(model.Annotation))
        return cls(**kwargs)

    def identifiable(self, cls, elem, **kwargs):
        """Create a IdentifiableArtefact of `cls` from `elem` and `kwargs`."""
        setdefault_attrib(kwargs, elem, "id", "urn", "uri")
        return self.annotable(cls, elem, **kwargs)

    def nameable(self, cls, elem, **kwargs):
        """Create a NameableArtefact of `cls` from `elem` and `kwargs`.

        Collects all parsed :class:`.InternationalString` localizations of <com:Name>
        and <com:Description>.
        """
        obj = self.identifiable(cls, elem, **kwargs)
        if elem is not None:
            add_localizations(obj.name, self.pop_all("Name"))
            add_localizations(obj.description, self.pop_all("Description"))
        return obj

    def maintainable(self, cls, elem, **kwargs):
        """Create or retrieve a MaintainableArtefact of `cls` from `elem` and `kwargs`.

        Following the SDMX-IM class hierarchy, :meth:`maintainable` calls
        :meth:`nameable`, which in turn calls :meth:`identifiable`, etc. (Since no
        concrete class is versionable but not maintainable, no separate method is
        created, for better performance). For all of these methods:

        - Already-parsed items are removed from the stack only if `elem` is not
          :obj:`None`.
        - `kwargs` (e.g. 'id') take precedence over any values retrieved from
          attributes of `elem`.

        If `elem` is None, :meth:`maintainable` returns a MaintainableArtefact with
        the is_external_reference attribute set to :obj:`True`. Subsequent calls with
        the same object ID will return references to the same object.
        """
        kwargs.setdefault("is_external_reference", elem is None)
        setdefault_attrib(kwargs, elem, "isExternalReference", "isFinal", "version")
        kwargs["is_final"] = kwargs.get("is_final", None) == "true"

        # Create a candidate object
        obj = self.nameable(cls, elem, **kwargs)

        try:
            # Retrieve the Agency.id for obj.maintainer
            maint = self.get_single(model.Agency, elem.attrib["agencyID"])
        except (AttributeError, KeyError):
            pass
        else:
            # Elem contains a maintainer ID
            if maint is None:
                # …but it did not correspond to an existing object; create one
                maint = model.Agency(id=elem.attrib["agencyID"])
                self.push(maint)
                # This object is never collected; ignore it at end of parsing
                self.ignore.add(id(maint))
            obj.maintainer = maint

        # Maybe retrieve an existing object of the same class and ID
        existing = self.get_single(cls, obj.id)

        if existing and (
            existing.compare(obj, strict=True) or existing.urn == pandasdmx.urn.make(obj)
        ):
            if elem is not None:
                # Previously an external reference, now concrete
                existing.is_external_reference = False

                # Update `existing` from `obj` to preserve references
                # If `existing` was a forward reference <Ref/>, its URN was not stored.
                for attr in list(kwargs.keys()) + ["urn"]:
                    # log.info(
                    #     f"Updating {attr} {getattr(existing, attr)} "
                    #     f"{getattr(obj, attr)}"
                    # )
                    setattr(existing, attr, getattr(obj, attr))

            # Discard the candidate
            obj = existing
        elif obj.is_external_reference:
            # A new external reference. Ensure it has a URN.
            obj.urn = obj.urn or pandasdmx.urn.make(obj)
            # Push onto the stack to be located by next calls
            self.push(obj)

        return obj


# Parsers for pandasdmx.message classes


@start(
    "mes:Error mes:GenericData mes:GenericTimeSeriesData mes:StructureSpecificData "
    "mes:StructureSpecificTimeSeriesData"
)
@start("mes:Structure", only=False)
def _message(reader, elem):
    """Start of a Message."""
    # <mes:Structure> within <mes:Header> of a data message is handled by
    # _header_structure() below.
    if getattr(elem.getparent(), "tag", None) == qname("mes", "Header"):
        return

    ss_without_dsd = False

    # With 'dsd' argument, the message should be structure-specific
    if (
        "StructureSpecific" in elem.tag
        and reader.get_single(model.DataStructureDefinition) is None
    ):
        log.warning(f"xml.Reader got no dsd=… argument for {QName(elem).localname}")
        ss_without_dsd = True
    elif "StructureSpecific" not in elem.tag and reader.get_single(
        model.DataStructureDefinition
    ):
        log.info("Use supplied dsd=… argument for non–structure-specific message")

    # Store values for other methods
    reader.push("SS without DSD", ss_without_dsd)
    if "Data" in elem.tag:
        reader.push("DataSetClass", model.get_class(f"{QName(elem).localname}Set"))

    # Instantiate the message object
    cls = class_for_tag(elem.tag)
    return cls()


@end("mes:Header")
def _header(reader, elem):
    # Attach to the Message
    header = message.Header(
        extracted=reader.pop_single("Extracted") or None,
        id=reader.pop_single("ID") or None,
        prepared=reader.pop_single("Prepared") or None,
        reporting_begin=reader.pop_single("ReportingBegin") or None,
        reporting_end=reader.pop_single("ReportingEnd") or None,
        receiver=reader.pop_single("Receiver") or None,
        sender=reader.pop_single("Sender") or None,
        test=str(reader.pop_single("Test")).lower() == "true",
    )
    add_localizations(header.source, reader.pop_all("Source"))

    reader.get_single(message.Message, subclass=True).header = header

    # TODO add these to the Message class
    # Appearing in data messages from WB_WDI and the footer.xml specimen
    reader.pop_all("DataSetAction")
    reader.pop_all("DataSetID")
    # Apparing in the footer.xml specimen
    reader.pop_all("Timezone")


@end("mes:Receiver mes:Sender")
def _header_org(reader, elem):
    reader.push(
        elem,
        reader.nameable(
            class_for_tag(elem.tag), elem, contact=reader.pop_all(model.Contact)
        ),
    )


@end("mes:Structure", only=False)
def _header_structure(reader, elem):
    """<mes:Structure> within <mes:Header> of a DataMessage."""
    # The root node of a structure message is handled by _message(), above.
    if elem.getparent() is None:
        return

    msg = reader.get_single(message.DataMessage)

    # Retrieve a DSD supplied to the parser, e.g. for a structure specific message
    provided_dsd = reader.get_single(model.DataStructureDefinition)

    # Resolve the <com:Structure> child to a DSD, maybe is_external_reference=True
    header_dsd = reader.pop_resolved_ref("Structure")

    # Resolve the <str:StructureUsage> child, if any, and remove it from the stack
    header_su = reader.pop_resolved_ref("StructureUsage")
    reader.pop_single(model.StructureUsage)

    if provided_dsd:
        dsd = provided_dsd
    else:
        if header_su:
            # The header gives a StructureUsage object, but it really refers to a DSD
            su_dsd = reader.maintainable(
                model.DataStructureDefinition,
                None,
                id=header_su.id,
                maintainer=header_su.maintainer,
                version=header_su.version,
            )

        if header_dsd:
            if header_su:
                assert header_dsd == su_dsd
            dsd = header_dsd
        elif header_su:
            reader.push(su_dsd)
            dsd = su_dsd
        else:
            raise RuntimeError

        # Store as an object that won't cause a parsing error if it is left over
        reader.ignore.add(id(dsd))

    # Store
    msg.dataflow.structure = dsd

    # Store under the structure ID, so it can be looked up by that ID
    reader.push(elem.attrib["structureID"], dsd)

    try:
        # Information about the 'dimension at observation level'
        dim_at_obs = elem.attrib["dimensionAtObservation"]
    except KeyError:
        pass
    else:
        # Store
        if dim_at_obs == "AllDimensions":
            # Use a singleton object
            dim = model.AllDimensions
        elif provided_dsd:
            # Use existing dimension from the provided DSD
            dim = dsd.dimensions.get(dim_at_obs)
        else:
            # Force creation of the 'dimension at observation' level
            dim = dsd.dimensions.getdefault(
                dim_at_obs,
                cls=(
                    model.TimeDimension
                    if "TimeSeries" in elem.getparent().getparent().tag
                    else model.Dimension
                ),
                # TODO later, reduce this
                order=maxsize,
            )
        msg.observation_dimension = dim


@end("footer:Footer")
def _footer(reader, elem):
    # Get attributes from the child <footer:Messsage>
    args = dict()
    setdefault_attrib(args, elem[0], "code", "severity")
    if "code" in args:
        args["code"] = int(args["code"])

    reader.get_single(message.Message, subclass=True).footer = message.Footer(
        text=list(map(model.InternationalString, reader.pop_all("Text"))), **args
    )


@end("mes:Structures")
def _structures(reader, elem):
    """End of a structure message."""
    msg = reader.get_single(message.StructureMessage)

    # Populate dictionaries by ID
    for attr, name in (
        ("categorisation", model.Categorisation),
        ("category_scheme", model.CategoryScheme),
        ("codelist", model.Codelist),
        ("concept_scheme", model.ConceptScheme),
        ("constraint", model.ContentConstraint),
        ("dataflow", model.DataflowDefinition),
        ("organisation_scheme", model.OrganisationScheme),
        ("provisionagreement", model.ProvisionAgreement),
        ("structure", model.DataStructureDefinition),
    ):
        for obj in reader.pop_all(name, subclass=True):
            getattr(msg, attr)[obj.id] = obj


# Parsers for sdmx.model classes
# §3.2: Base structures


@end(
    "com:AnnotationTitle com:AnnotationType com:AnnotationURL com:None com:URN "
    "com:Value mes:DataSetAction mes:DataSetID mes:Email mes:ID mes:Test mes:Timezone "
    "str:Email str:Telephone str:URI"
)
def _text(reader, elem):
    reader.push(elem, elem.text)


@end("mes:Extracted mes:Prepared mes:ReportingBegin mes:ReportingEnd")
def _datetime(reader, elem):
    text, n = re.subn(r"(.*\.)(\d{6})\d+(\+.*)", r"\1\2\3", elem.text)
    if n > 0:
        log.debug(f"Truncate sub-microsecond time in <{QName(elem).localname}>")

    reader.push(elem, isoparse(text))


@end(
    "com:AnnotationText com:Name com:Description com:Text mes:Source mes:Department "
    "mes:Role str:Department str:Role"
)
def _localization(reader, elem):
    reader.push(
        elem, (elem.attrib.get(qname("xml:lang"), model.DEFAULT_LOCALE), elem.text)
    )


@end(
    "com:Structure com:StructureUsage str:AttachmentGroup str:ConceptIdentity "
    "str:DimensionReference str:Parent str:Source str:Structure str:StructureUsage "
    "str:Target str:Enumeration"
)
def _ref(reader, elem):
    cls_hint = None
    if "Parent" in elem.tag:
        # Use the *grand*-parent of the <Ref> or <URN> for a class hint
        cls_hint = class_for_tag(elem.getparent().tag)

    reader.push(QName(elem).localname, Reference(elem, cls_hint))


@end("com:Annotation")
def _a(reader, elem):
    args = dict(
        title=reader.pop_single("AnnotationTitle"),
        type=reader.pop_single("AnnotationType"),
        url=reader.pop_single("AnnotationURL"),
    )

    # Optional 'id' attribute
    setdefault_attrib(args, elem, "id")

    a = model.Annotation(**args)
    add_localizations(a.text, reader.pop_all("AnnotationText"))

    return a


# §3.5: Item Scheme


@start(
    "str:Agency str:Code str:Category str:Concept str:DataConsumer str:DataProvider",
    only=False,
)
def _item_start(reader, elem):
    # Avoid stealing the name & description of the parent ItemScheme from the stack
    # TODO check this works for annotations

    try:
        if elem[0].tag in ("Ref", "URN"):
            # `elem` is a reference, so it has no name/etc.; don't stash
            return
    except IndexError:
        # No child elements; stash() anyway, but it will be a no-op
        pass

    reader.stash("Name", "Description")


@end("str:Agency str:Code str:Category str:DataConsumer str:DataProvider", only=False)
def _item(reader, elem):
    try:
        # <str:DataProvider> may be a reference, e.g. in <str:ConstraintAttachment>
        return Reference(elem)
    except NotReference:
        pass

    cls = class_for_tag(elem.tag)
    item = reader.nameable(cls, elem)

    # Hierarchy is stored in two ways

    # (1) XML sub-elements of the parent. These have already been parsed.
    for e in elem:
        if e.tag == elem.tag:
            # Found 1 child XML element with same tag → claim 1 child object
            item.append_child(reader.pop_single(cls))

    # (2) through <str:Parent>
    parent = reader.pop_resolved_ref("Parent")
    if parent:
        parent.append_child(item)

    # Agency only
    try:
        item.contact = reader.pop_all(model.Contact)
    except ValueError:
        # NB this is a ValueError from pydantic, rather than AttributeError from Python
        pass

    reader.unstash()
    return item


@end(
    "str:AgencyScheme str:Codelist str:ConceptScheme str:CategoryScheme "
    "str:DataConsumerScheme str:DataProviderScheme",
)
def _itemscheme(reader, elem):
    cls = class_for_tag(elem.tag)

    is_ = reader.maintainable(cls, elem)

    # Iterate over all Item objects *and* their children
    iter_all = chain(*[iter(item) for item in reader.pop_all(cls._Item)])

    # Set of objects already added to `items`
    seen = dict()

    # Flatten the list, with each item appearing only once
    for i in filter(lambda i: i not in seen, iter_all):
        try:
            is_.append(seen.setdefault(i, i))
        except ValueError:  # pragma: no cover
            # Existing item, e.g. created by a reference in the same message
            # TODO "no cover" since this doesn't occur in the test suite; check whether
            #      this try/except can be removed.
            pass

    return is_


# §3.6: Structure


@end("str:EnumerationFormat str:TextFormat")
def _facet(reader, elem):
    attrib = copy(elem.attrib)

    # Parse facet value type; SDMX-ML default is 'String'
    fvt = attrib.pop("textType", "String")

    f = model.Facet(
        # Convert case of the value. In XML, first letter is uppercase; in
        # the spec and Python enum, lowercase.
        value_type=model.FacetValueType[fvt[0].lower() + fvt[1:]],
        # Other attributes are for Facet.type, an instance of FacetType. Convert
        # the attribute name from camelCase to snake_case
        type=model.FacetType(**{to_snake(key): val for key, val in attrib.items()}),
    )
    reader.push(elem, f)


@end("str:CoreRepresentation str:LocalRepresentation")
def _rep(reader, elem):
    return model.Representation(
        enumerated=reader.pop_resolved_ref("Enumeration"),
        non_enumerated=list(
            chain(reader.pop_all("EnumerationFormat"), reader.pop_all("TextFormat"))
        ),
    )


# §4.4: Concept Scheme


@end("str:Concept", only=False)
def _concept(reader, elem):
    concept = _item(reader, elem)
    concept.core_representation = reader.pop_single(model.Representation)
    return concept


# §3.3: Basic Inheritance


@end(
    "str:Attribute str:Dimension str:GroupDimension str:MeasureDimension "
    "str:PrimaryMeasure str:TimeDimension"
)
def _component(reader, elem):
    try:
        # May be a reference
        return Reference(elem)
    except NotReference:
        pass

    # Object class: {,Measure,Time}Dimension or DataAttribute
    cls = class_for_tag(elem.tag)

    args = dict(
        concept_identity=reader.pop_resolved_ref("ConceptIdentity"),
        local_representation=reader.pop_single(model.Representation),
    )
    try:
        args["order"] = int(elem.attrib["position"])
    except KeyError:
        pass

    # DataAttribute only
    ar = reader.pop_all(model.AttributeRelationship, subclass=True)
    if len(ar):
        assert len(ar) == 1
        args["related_to"] = ar[0]

    if cls is model.PrimaryMeasure and "id" not in elem.attrib:
        # SDMX spec §3A, part III, p.140: “The id attribute holds an explicit
        # identification of the component. If this identifier is not supplied, then it
        # is assumed to be the same as the identifier of the concept referenced from
        # the concept identity.”
        args["id"] = args["concept_identity"].id

    return reader.identifiable(cls, elem, **args)


@end("str:AttributeList str:DimensionList str:Group str:MeasureList")
def _cl(reader, elem):
    try:
        # <str:Group> may be a reference
        return Reference(elem, cls_hint=model.GroupDimensionDescriptor)
    except NotReference:
        pass

    # Retrieve the DSD
    dsd = reader.peek("current DSD")
    assert dsd is not None

    # Retrieve the components
    args = dict(components=reader.pop_all(model.Component, subclass=True))

    # Determine the class
    localname = QName(elem).localname
    if localname == "Group":
        cls = model.GroupDimensionDescriptor

        # Replace components with references
        args["components"] = [
            dsd.dimensions.get(ref.target_id)
            for ref in reader.pop_all("DimensionReference")
        ]
    else:
        # SDMX-ML spec for, e.g. DimensionList: "The id attribute is
        # provided in this case for completeness. However, its value is
        # fixed to 'DimensionDescriptor'."
        cls = class_for_tag(elem.tag)
        args["id"] = elem.attrib.get("id", cls.__name__)

    cl = reader.identifiable(cls, elem, **args)

    try:
        # DimensionDescriptor only
        cl.assign_order()
    except AttributeError:
        pass

    # Assign to the DSD eagerly (instead of in _dsd_end()) for reference by next
    # ComponentList e.g. so that AttributeRelationship can reference the
    # DimensionDescriptor
    attr = {
        model.DimensionDescriptor: "dimensions",
        model.AttributeDescriptor: "attributes",
        model.MeasureDescriptor: "measures",
        model.GroupDimensionDescriptor: "group_dimensions",
    }.get(cl.__class__)
    if attr == "group_dimensions":
        getattr(dsd, attr)[cl.id] = cl
    else:
        setattr(dsd, attr, cl)


# §4.5: Category Scheme


@end("str:Categorisation")
def _cat(reader, elem):
    return reader.maintainable(
        model.Categorisation,
        elem,
        artefact=reader.pop_resolved_ref("Source"),
        category=reader.pop_resolved_ref("Target"),
    )


# §4.6: Organisations


@end("mes:Contact str:Contact")
def _contact(reader, elem):
    contact = model.Contact(
        telephone=reader.pop_single("Telephone"),
        uri=reader.pop_all("URI"),
        email=reader.pop_all("Email"),
    )
    add_localizations(contact.name, reader.pop_all("Name"))
    add_localizations(contact.org_unit, reader.pop_all("Department"))
    add_localizations(contact.responsibility, reader.pop_all("Role"))
    return contact


# §10.3: Constraints


@end("str:Key")
def _dk(reader, elem):
    return model.DataKey(
        included=elem.attrib.get("isIncluded", True),
        # Convert MemberSelection/MemberValue from _ms() to ComponentValue
        key_value={
            ms.values_for: model.ComponentValue(
                value_for=ms.values_for, value=ms.values.pop().value
            )
            for ms in reader.pop_all(model.MemberSelection)
        },
    )


@end("str:DataKeySet")
def _dks(reader, elem):
    return model.DataKeySet(
        included=elem.attrib["isIncluded"], keys=reader.pop_all(model.DataKey)
    )


@end("com:StartPeriod com:EndPeriod")
def _p(reader, elem):
    # Store by element tag name
    reader.push(
        elem,
        model.Period(
            is_inclusive=elem.attrib["isInclusive"], period=isoparse(elem.text)
        ),
    )


@end("com:TimeRange")
def _tr(reader, elem):
    return model.RangePeriod(
        start=reader.pop_single("StartPeriod"), end=reader.pop_single("EndPeriod")
    )


@end("com:Attribute com:KeyValue")
def _ms(reader, elem):
    """MemberSelection."""
    arg = dict(values_for=None)

    # Identify the component
    # Values are for either a Dimension or Attribute, based on tag name
    kind = {
        "KeyValue": ("dimensions", model.Dimension),
        "Attribute": ("attributes", model.DataAttribute),
    }.get(QName(elem).localname)

    try:
        # Navigate from the current ContentConstraint to a ConstrainableArtefact
        cc_content = reader.stack[Reference]
        assert len(cc_content) == 1, (cc_content, reader.stack, elem.attrib)
        obj = reader.resolve(next(iter(cc_content.values())))

        if isinstance(obj, model.DataflowDefinition):
            # The constrained DFD has a corresponding DSD, which has a Dimension- or
            # AttributeDescriptor
            cl = getattr(obj.structure, kind[0])
        elif isinstance(obj, model.DataStructureDefinition):
            # The DSD is constrained directly
            cl = getattr(obj, kind[0])
        else:
            log.warning(f"Not implemented: constraints attached to {type(obj)}")
            cl = None

        # Get the Component
        arg["values_for"] = cl.get(elem.attrib["id"])
    except AttributeError:
        # Failed because the ContentConstraint is attached to something, e.g.
        # DataProvider, that does not provide an association to a DSD. Try to get a
        # Component from the current scope with matching ID.
        arg["values_for"] = reader.get_single(
            kind[1], id=elem.attrib["id"], subclass=True
        )

    # Convert to SelectionValue
    mvs = reader.pop_all("Value")
    trv = reader.pop_all(model.TimeRangeValue)
    if mvs:
        arg["values"] = list(map(lambda v: model.MemberValue(value=v), mvs))
    elif trv:
        arg["values"] = trv
    else:
        raise RuntimeError

    if arg["values_for"] is None:
        log.warning(
            f"{cl} has no {kind[1].__name__} with ID {elem.attrib['id']}; XML element "
            "ignored and SelectionValues discarded"
        )
        return None
    else:
        return model.MemberSelection(**arg)


@end("str:CubeRegion")
def _cr(reader, elem):
    return model.CubeRegion(
        included=elem.attrib["include"],
        # Combine member selections for Dimensions and Attributes
        member={ms.values_for: ms for ms in reader.pop_all(model.MemberSelection)},
    )


@end("str:ContentConstraint")
def _cc(reader, elem):
    cr_str = elem.attrib["type"].lower().replace("allowed", "allowable")

    content = set()
    for ref in reader.pop_all(Reference):
        resolved = reader.resolve(ref)
        if resolved is None:
            log.warning(f"Unable to resolve ContentConstraint.content ref:\n  {ref}")
        else:
            content.add(resolved)

    return reader.nameable(
        model.ContentConstraint,
        elem,
        role=model.ConstraintRole(role=model.ConstraintRoleType[cr_str]),
        content=content,
        data_content_keys=reader.pop_single(model.DataKeySet),
        data_content_region=reader.pop_all(model.CubeRegion),
    )


# §5.2: Data Structure Definition


@end("str:AttributeRelationship")
def _ar(reader, elem):
    dsd = reader.peek("current DSD")

    if "None" in elem[0].tag:
        return model.NoSpecifiedRelationship

    # Iterate over parsed references to Components
    args = dict(dimensions=list())
    for ref in reader.pop_all(Reference):
        # Use the <Ref id="..."> to retrieve a Component from the DSD
        if issubclass(ref.target_cls, model.DimensionComponent):
            component = dsd.dimensions.get(ref.target_id)
            args["dimensions"].append(component)
        elif ref.target_cls is model.PrimaryMeasure:
            # Since <str:AttributeList> occurs before <str:MeasureList>, this is
            # usually a forward reference. We *could* eventually resolve it to confirm
            # consistency (the referenced ID is same as the PrimaryMeasure.id), but
            # that doesn't affect the returned value, since PrimaryMeasureRelationship
            # has no attributes.
            return model.PrimaryMeasureRelationship
        elif ref.target_cls is model.GroupDimensionDescriptor:
            args["group_key"] = dsd.group_dimensions[ref.target_id]

    ref = reader.pop_single("AttachmentGroup")
    if ref:
        args["group_key"] = dsd.group_dimensions[ref.target_id]

    if len(args["dimensions"]):
        return model.DimensionRelationship(**args)
    else:
        args.pop("dimensions")
        return model.GroupRelationship(**args)


@start("str:DataStructure", only=False)
def _dsd_start(reader, elem):
    try:
        # <str:DataStructure> may be a reference, e.g. in <str:ConstraintAttachment>
        return Reference(elem)
    except NotReference:
        pass

    # Get any external reference created earlier, or instantiate a new object.
    dsd = reader.maintainable(model.DataStructureDefinition, elem)

    if dsd not in reader.stack[model.DataStructureDefinition]:
        # A new object was created
        reader.push(dsd)

    # Store a separate reference to the current DSD
    reader.push("current DSD", dsd)


@end("str:DataStructure", only=False)
def _dsd_end(reader, elem):
    dsd = reader.pop_single("current DSD")

    if dsd:
        # Collect annotations, name, and description
        dsd.annotations = list(reader.pop_all(model.Annotation))
        add_localizations(dsd.name, reader.pop_all("Name"))
        add_localizations(dsd.description, reader.pop_all("Description"))


@end("str:Dataflow")
def _dfd(reader, elem):
    try:
        # <str:Dataflow> may be a reference, e.g. in <str:ConstraintAttachment>
        return Reference(elem)
    except NotReference:
        pass

    structure = reader.pop_resolved_ref("Structure")
    if structure is None:
        log.warning(
            "Not implemented: forward reference to:\n" + etree.tostring(elem).decode()
        )
        arg = {}
    else:
        arg = dict(structure=structure)

    # Create first to collect names
    return reader.maintainable(model.DataflowDefinition, elem, **arg)


# §5.4: Data Set


@end("gen:Attributes")
def _avs(reader, elem):
    ad = reader.get_single("DataSet").structured_by.attributes

    result = {}
    for e in elem.iterchildren():
        da = ad.getdefault(e.attrib["id"])
        result[da.id] = model.AttributeValue(value=e.attrib["value"], value_for=da)

    reader.push("Attributes", result)


@end("gen:ObsKey gen:GroupKey gen:SeriesKey")
def _key(reader, elem):
    cls = class_for_tag(elem.tag)

    kv = {e.attrib["id"]: e.attrib["value"] for e in elem.iterchildren()}

    dsd = reader.get_single("DataSet").structured_by

    return dsd.make_key(cls, kv, extend=True)


@end("gen:Series")
def _series(reader, elem):
    ds = reader.get_single("DataSet")
    sk = reader.pop_single(model.SeriesKey)
    sk.attrib.update(reader.pop_single("Attributes") or {})
    ds.add_obs(reader.pop_all(model.Observation), sk)


@end(":Series")
def _series_ss(reader, elem):
    ds = reader.get_single("DataSet")
    ds.add_obs(
        reader.pop_all(model.Observation),
        ds.structured_by.make_key(
            model.SeriesKey, elem.attrib, extend=reader.peek("SS without DSD")
        ),
    )


@end("gen:Group")
def _group(reader, elem):
    ds = reader.get_single("DataSet")

    gk = reader.pop_single(model.GroupKey)
    gk.attrib.update(reader.pop_single("Attributes") or {})

    # Group association of Observations is done in _ds_end()
    ds.group[gk] = []


@end(":Group")
def _group_ss(reader, elem):
    ds = reader.get_single("DataSet")
    attrib = copy(elem.attrib)

    group_id = attrib.pop(qname("xsi", "type"), None)

    gk = ds.structured_by.make_key(
        model.GroupKey, attrib, extend=reader.peek("SS without DSD")
    )

    if group_id:
        # The group_id is in a format like "foo:GroupName", where "foo" is an XML
        # namespace
        ns, group_id = group_id.split(":")
        assert ns in elem.nsmap

        try:
            gk.described_by = ds.structured_by.group_dimensions[group_id]
        except KeyError:
            if not reader.peek("SS without DSD"):
                raise

    ds.group[gk] = []


@end("gen:Obs")
def _obs(reader, elem):
    dim_at_obs = reader.get_single(message.DataMessage).observation_dimension
    dsd = reader.get_single("DataSet").structured_by

    args = dict()

    for e in elem.iterchildren():
        localname = QName(e).localname
        if localname == "Attributes":
            args["attached_attribute"] = reader.pop_single("Attributes")
        elif localname == "ObsDimension":
            # Mutually exclusive with ObsKey
            args["dimension"] = dsd.make_key(
                model.Key, {dim_at_obs.id: e.attrib["value"]}
            )
        elif localname == "ObsKey":
            # Mutually exclusive with ObsDimension
            args["dimension"] = reader.pop_single(model.Key)
        elif localname == "ObsValue":
            args["value"] = e.attrib["value"]

    return model.Observation(**args)


@end(":Obs")
def _obs_ss(reader, elem):
    # True if the user failed to provide a DSD to use in parsing structure-specific data
    extend = reader.peek("SS without DSD")

    # Retrieve the PrimaryMeasure from the DSD for the current data set
    dsd = reader.get_single("DataSet").structured_by

    try:
        # Retrieve the PrimaryMeasure in a supplied DSD, or one created in a previous
        # call to _obs_ss()
        pm = dsd.measures[0]
    except IndexError:
        # No measures in the DSD
        if extend:
            # Create one, assuming the ID OBS_VALUE
            # TODO also add an external reference to the SDMX cross-domain concept
            pm = model.PrimaryMeasure(id="OBS_VALUE")
            dsd.measures.append(pm)
        else:  # pragma: no cover
            raise  # DSD was provided but lacks a PrimaryMeasure

    # StructureSpecificData message—all information stored as XML attributes of the
    # <Observation>
    attrib = copy(elem.attrib)

    # Observation value from an attribute; usually "OBS_VALUE"
    value = attrib.pop(pm.id, None)

    # Extend the DSD if the user failed to provide it
    key = dsd.make_key(model.Key, attrib, extend=extend)

    # Remove attributes from the Key to be attached to the Observation
    aa = key.attrib
    key.attrib = {}

    return model.Observation(
        dimension=key, value=value, value_for=pm, attached_attribute=aa
    )


@start("mes:DataSet", only=False)
def _ds_start(reader, elem):
    # Create an instance of a DataSet subclass
    ds = reader.peek("DataSetClass")()

    # Store a reference to the DSD that structures the data set
    id = elem.attrib.get("structureRef", None) or elem.attrib.get(
        qname("data:structureRef"), None
    )
    ds.structured_by = reader.get_single(id)

    if not ds.structured_by:  # pragma: no cover
        raise RuntimeError("No DSD when creating DataSet")

    reader.push("DataSet", ds)


@end("mes:DataSet", only=False)
def _ds_end(reader, elem):
    ds = reader.pop_single("DataSet")

    # Collect attributes attached to the data set
    ds.attrib.update(reader.pop_single("Attributes") or {})

    # Collect observations not grouped by SeriesKey
    ds.add_obs(reader.pop_all(model.Observation))

    # Add any group associations not made above in add_obs() or in _series()
    for obs in ds.obs:
        ds._add_group_refs(obs)

    # Add the data set to the message
    reader.get_single(message.DataMessage).data.append(ds)


# §11: Data Provisioning


@end("str:ProvisionAgreement")
def _pa(reader, elem):
    return reader.maintainable(
        model.ProvisionAgreement,
        elem,
        structure_usage=reader.pop_resolved_ref("StructureUsage"),
        data_provider=reader.pop_resolved_ref(Reference),
    )
