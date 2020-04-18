"""SDMXML v2.1 reader."""
# See comments on the Reader() class for implementation details
from collections import defaultdict
from copy import copy
from inspect import isclass
from itertools import chain
import logging
import re

from lxml import etree
from lxml.etree import QName, XPath

from pandasdmx.exceptions import ParseError, XMLParseError
from pandasdmx.message import (
    DataMessage, ErrorMessage, Footer, Header, StructureMessage,
    )
import pandasdmx.model
from pandasdmx.model import (  # noqa: F401
    DEFAULT_LOCALE, Agency, AgencyScheme, AllDimensions, Annotation,
    AttributeDescriptor, NoSpecifiedRelationship, PrimaryMeasureRelationship,
    DimensionRelationship, AttributeValue, Categorisation, Category,
    CategoryScheme, Code, Codelist, ComponentValue, Concept, ConceptScheme,
    Contact, ContentConstraint, ConstraintRole, ConstraintRoleType, CubeRegion,
    DataAttribute, DataflowDefinition, DataKey, DataKeySet, DataProvider,
    DataProviderScheme, DataSet, DataStructureDefinition, Dimension,
    DimensionDescriptor, Facet, FacetValueType, GroupDimensionDescriptor,
    GroupKey, IdentifiableArtefact, InternationalString, ItemScheme,
    MaintainableArtefact, MeasureDescriptor, MeasureDimension, MemberSelection,
    MemberValue, Key, Observation, PrimaryMeasure, ProvisionAgreement,
    Representation, SeriesKey, TimeDimension, UsageStatus,
    )

from pandasdmx.reader import BaseReader


log = logging.getLogger(__name__)


# Regular expression for URNs used as references
URN = re.compile(r'urn:sdmx:org\.sdmx\.infomodel'
                 r'\.(?P<package>[^\.]*)'
                 r'\.(?P<class>[^=]*)=((?P<agency>[^:]*):)?'
                 r'(?P<id>[^\(\.]*)(\((?P<version>[\d\.]*)\))?'
                 r'(\.(?P<item_id>.*))?')


# XML namespaces
_base_ns = 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1'
NS = {
    'com': f'{_base_ns}/common',
    'data': f'{_base_ns}/data/structurespecific',
    'str': f'{_base_ns}/structure',
    'mes': f'{_base_ns}/message',
    'gen': f'{_base_ns}/data/generic',
    'footer': f'{_base_ns}/message/footer',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }


def qname(ns, name):
    """Return a fully-qualified tag *name* in namespace *ns*."""
    return QName(NS[ns], name)


_TO_SNAKE_RE = re.compile('([A-Z]+)')


def to_snake(value):
    """Convert *value* from lowerCamelCase to snake_case."""
    return _TO_SNAKE_RE.sub(r'_\1', value).lower()


# Mapping tag names → Message classes
MESSAGE = {qname('mes', name): cls for name, cls in (
    ('Structure', StructureMessage),
    ('GenericData', DataMessage),
    ('GenericTimeSeriesData', DataMessage),
    ('StructureSpecificData', DataMessage),
    ('StructureSpecificTimeSeriesData', DataMessage),
    ('Error', ErrorMessage),
    )}


# XPath expressions for parse_header()
HEADER_XPATH = {key: XPath(expr, namespaces=NS, smart_strings=False) for
                key, expr in (
    ('id', 'mes:ID/text()'),
    ('prepared', 'mes:Prepared/text()'),
    ('sender', 'mes:Sender/@*'),
    ('receiver', 'mes:Receiver/@*'),
    ('structure_id', 'mes:Structure/@structureID'),
    ('dim_at_obs', 'mes:Structure/@dimensionAtObservation'),
    # 'Structure' vs 'StructureUsage' varies across XML specimens.
    ('structure_ref_id', '(mes:Structure/com:Structure/Ref/@id | '
                         'mes:Structure/com:StructureUsage/Ref/@id)[1]'),
    ('structure_ref_agencyid', '(mes:Structure/com:Structure/Ref/@agencyID | '
                               'mes:Structure/com:StructureUsage/Ref/'
                               '@agencyID)[1]'),
    ('structure_ref_version', '(mes:Structure/com:Structure/Ref/@version | '
                              'mes:Structure/com:StructureUsage/Ref/'
                              '@version)[1]'),
    ('structure_ref_urn', 'mes:Structure/com:Structure/URN/text()'),
    )}


# For Reader._parse(): tag name → Reader.parse_[…] method to use
# TODO make this data structure more compact/avoid repetition
METHOD = {
    'AnnotationText': 'international_string',
    'Name': 'international_string',
    'Department': 'international_string',
    'Description': 'international_string',
    'Role': 'international_string',
    'Text': 'international_string',

    'DimensionList': 'componentlist',
    'AttributeList': 'componentlist',
    'MeasureList': 'componentlist',

    'CoreRepresentation': 'representation',
    'LocalRepresentation': 'representation',

    'AnnotationType': 'text',
    'AnnotationTitle': 'text',
    'AnnotationURL': 'text',
    'Email': 'text',
    'None': 'text',
    'Telephone': 'text',
    'URI': 'text',
    'URN': 'text',
    'Value': 'text',

    'ObsKey': 'key',
    'SeriesKey': 'key',
    'GroupKey': 'key',

    'AgencyScheme': 'orgscheme',
    'DataproviderScheme': 'orgscheme',

    'Agency': 'organisation',
    'DataProvider': 'organisation',

    'KeyValue': 'memberselection',

    'TextFormat': 'facet',
    'EnumerationFormat': 'facet',

    'MeasureDimension': 'dimension',
    'TimeDimension': 'dimension',

    # Tags that are bare containers for other XML elements; skip entirely
    'Annotations': 'SKIP',
    'CategorySchemes': 'SKIP',
    'Categorisations': 'SKIP',
    'Codelists': 'SKIP',
    'Concepts': 'SKIP',
    'Constraints': 'SKIP',
    'Dataflows': 'SKIP',
    'DataStructures': 'SKIP',
    'DataStructureComponents': 'SKIP',
    'Footer': 'SKIP',
    'OrganisationSchemes': 'SKIP',
    'ProvisionAgreements': 'SKIP',

    # Tag names that only ever contain references
    'AttachmentGroup': 'ref',
    'DimensionReference': 'ref',
    'Parent': 'ref',
    'Source': 'ref',
    'Structure': 'ref',  # str:Structure, not mes:Structure
    'Target': 'ref',
    # 'ConstraintAttachment': 'ref',
    'Enumeration': 'ref',
    }


# Mappings from SDMX-ML 'package' to contained classes
PACKAGE_CLASS = {
    'base': {Agency, AgencyScheme, DataProvider},
    'categoryscheme': {Category, Categorisation, CategoryScheme},
    'codelist': {Code, Codelist},
    'conceptscheme': {Concept, ConceptScheme},
    'datastructure': {DataflowDefinition, DataStructureDefinition},
    'registry': {ContentConstraint, ProvisionAgreement},
    }


def get_class(package, cls):
    """Return a class object for string *cls* and *package* names."""
    if isinstance(cls, str):
        if cls in 'Dataflow DataStructure':
            cls += 'Definition'
        cls = getattr(pandasdmx.model, cls)

    assert cls in PACKAGE_CLASS[package], \
        f'Package {package!r} invalid for {cls}'

    return cls


def wrap(value):
    """Return *value* as a list.

    Reader._parse(elem, unwrap=True) returns single children of *elem* as bare
    objects. wrap() ensures they are a list.
    """
    return value if isinstance(value, list) else [value]


def add_localizations(target, values):
    """Add localized strings from *values* to *target*."""
    if isinstance(values, tuple) and len(values) == 2:
        values = [values]
    target.localizations.update({locale: label for locale, label in values})


class Reparse(Exception):
    """Raised for a forward reference to trigger reparsing."""
    pass


# Reader operates by recursion through the _parse() method:
#
# - _parse(elem) uses the XML tag name of elem, plus METHOD, to find a method
#    like Reader.parse_X().
# - parse_X(elem) is called. These methods perform similar tasks such as:
#   - Create an instance of a pandasdmx.model class,
#   - Recursively:
#     - call _parse() on the children of elem,
#     - call _named(), which also creates an instance of a NameableArtefact,
#   - Handle the returned values (i.e. parsed XML child elements) and attach
#     them to the model object,
#   - Handle the XML attributes of elem and attach these to the model object,
#   - ``assert len(values) == 0`` or similar to assert that all parsed child
#     elements and/or attributes have been consumed,
#   - Return the parsed model object to be used further up the recursive stack.
#
class Reader(BaseReader):
    """Read SDMX-ML 2.1 and expose it as instances from :mod:`pandasdmx.model`.

    The implementation is recursive, and depends on:

    - :meth:`_parse`, :meth:`_named` and :meth:`_maintained`.
    - State variables :attr:`_current`, :attr:`_stack, :attr:`_index`.

    Parameters
    ----------
    dsd : :class:`~.DataStructureDefinition`
        For “structure-specific” `format`=``XML`` messages only.
    """
    # State variables for reader

    # Stack (0 = top) of tag names being parsed by _parse().
    # Tag parsers may examine the stack to determine context for parsing.
    _stack = []

    # Map of (class name, id) → pandasdmx.model object.
    # Only IdentifiableArtefacts should be stored. See _maintained().
    _index = {}

    # Similar to _index, but specific to the current scope.
    _current = {}

    def read_message(self, source, dsd=None):
        # Root XML element
        root = etree.parse(source).getroot()

        # Message class
        try:
            cls = MESSAGE[root.tag]
        except KeyError:
            msg = 'Unrecognized message root element {!r}'.format(root.tag)
            raise ParseError(msg) from None

        # Reset state
        self._stack = []
        self._index = {}
        self._current = {}

        # With 'dsd' argument, the message should be structure-specific
        if dsd is not None:
            if 'StructureSpecific' not in root.tag:
                log.warning('Ambiguous: dsd= argument for non-structure-'
                            'specific message')
            self._index[('DataStructureDefinition', dsd.id)] = dsd

        # Parse the tree
        values = self._parse(root)

        # Instantiate the message object
        msg = cls()

        # Store the header
        header = values.pop('header', None)
        if header is None and 'errormessage' in values:
            # An error message
            msg.header = Header()

            # Error message attributes resemble footer attributes
            values['footer'] = Footer(**values.pop('errormessage'))
        elif len(header) == 2:
            # Length-2 list includes DFD/DSD reference
            msg.header, msg.dataflow = header
            msg.observation_dimension = self._obs_dim
        else:
            # No DFD in the header, e.g. for a StructureMessage
            msg.header = header[0]

        # Store the footer
        msg.footer = values.pop('footer', None)

        # Finalize according to the message type
        if cls is DataMessage:
            # Simply store the datasets
            msg.data.extend(wrap(values.pop('dataset', [])))
        elif cls is StructureMessage:
            structures = values.pop('structures')

            # Populate dictionaries by ID
            for attr, name in (
                    ('dataflow', 'dataflows'),
                    ('codelist', 'codelists'),
                    ('constraint', 'constraints'),
                    ('structure', 'datastructures'),
                    ('category_scheme', 'categoryschemes'),
                    ('concept_scheme', 'concepts'),
                    ('organisation_scheme', 'organisationschemes'),
                    ('provisionagreement', 'provisionagreements'),
                    ):
                for obj in structures.pop(name, []):
                    getattr(msg, attr)[obj.id] = obj

            # Check, but do not store, Categorisations

            # Assemble a list of external categoryschemes
            ext_cs = []
            for key, cs in self._index.items():
                if key[0] == 'CategoryScheme' and cs.is_external_reference:
                    ext_cs.append(cs)

            for c in structures.pop('categorisations', []):
                if not isinstance(c.artefact, DataflowDefinition):
                    continue
                assert c.artefact in msg.dataflow.values()

                missing_cs = True
                for cs in chain(msg.category_scheme.values(), ext_cs):
                    if c.category in cs:
                        missing_cs = False
                        if cs.is_external_reference:
                            # Store the externally-referred CategoryScheme
                            msg.category_scheme[cs.id] = cs
                        break

                assert not missing_cs

            assert len(structures) == 0, structures

        assert len(values) == 0, values
        return msg

    def _parse(self, elem, unwrap=True):
        """Recursively parse the XML *elem* and return pandasdmx.model objects.

        Methods like 'Reader.parse_attribute()' are called for XML elements
        with tag names like '<ns:Attribute>'; each emits pandasdmx.model
        objects.

        If *unwrap* is True (the default), then single-entry lists are returned
        as bare objects.
        """
        # Container for results
        results = defaultdict(list)

        # Store state: tag name for the elem
        self._stack.append(QName(elem).localname)

        # Parse each child
        reparse = []  # Elements to reparse after the first pass
        reparse_limit = 2 * len(elem)
        for i, child in enumerate(chain(elem, reparse)):
            if i > reparse_limit:
                # Probably repeated failure to parse the same elements, which
                # would lead to an infinite loop
                raise ValueError(f'Unable to parse elements {reparse!r}')

            # Tag name for the child
            tag_name = QName(child).localname

            # Invoke the parser for this element
            try:
                # Get the name of the parser method
                how = METHOD.get(tag_name, tag_name)

                if how == 'SKIP':
                    # Element is a bare container for other elements; parse its
                    # children directly
                    result = list(chain(*self._parse(child, unwrap=False)
                                        .values()))
                elif how == 'ref' or (len(child) == 1 and
                                      child[0].tag == 'Ref'):
                    # Element contains a reference
                    # Parse the reference; may raise Reparse (below)
                    result = [self.parse_ref(child[0], parent=tag_name)]
                else:
                    # All other elements
                    result = [getattr(self, f'parse_{how}'.lower())(child)]
            except Reparse as r:
                # Raise one level beyond the original to reparse <Parent><Ref>
                # instead of <Ref>
                if r.args[0] < 1:
                    self._stack.pop()
                    raise Reparse(r.args[0] + 1)

                # Add to the queue to be reparsed on the second pass
                reparse.append(child)

                # Continue with next child element
                continue
            except XMLParseError:
                raise  # Re-raise without adding to the stack
            except Exception as e:
                # Other exception, convert to XMLParseError
                raise XMLParseError(self, child) from e
                # NOTE to debug, use:
                # raise e

            # Add objects with IDs to the appropriate index
            self._add_to_index(result)

            # Store the parsed elements
            results[tag_name.lower()].extend(result)

        # Restore state
        self._clear_current(self._stack.pop())

        if unwrap:
            # Unwrap every value in results that is a length-1 list
            results = {k: v[0] if len(v) == 1 else v for k, v in
                       results.items()}

        return results

    def _add_to_index(self, items):
        """Add objects with IDs to the appropriate index."""
        for item in items:
            if isinstance(item, MaintainableArtefact) and not \
                    item.is_external_reference:
                # Global index for MaintainableArtefacts
                self._index[(item.__class__.__name__, item.id)] = item
            elif isinstance(item, IdentifiableArtefact):
                # Current scope index for IdentifiableArtefacts
                self._current[(item.__class__, item.id)] = item

    def _maintained(self, cls=None, id=None, urn=None, **kwargs):
        """Retrieve or instantiate a MaintainableArtefact of *cls* with *ids.

        If the object has been parsed (i.e. is in :attr:`_index`), it is
        returned; if not and `match_subclass` is :obj:`False`, it is
        instantiated with ``is_external_reference=True``, passing `kwargs`.

        If *urn* is given, it is used to determine *cls* and *id*, per the URN
        regular expression.
        """
        if urn:
            match = URN.match(urn).groupdict()
            cls = get_class(match['package'], match['class'])
            id = match['id']

            # Re-add the URN to the kwargs
            kwargs['urn'] = urn

        key = (cls.__name__, id) if isclass(cls) else (cls, id)

        # Maybe create a new object
        if key not in self._index:
            if not isclass(cls):
                raise TypeError(f'cannot instantiate from {cls!r}')
            elif not issubclass(cls, MaintainableArtefact):
                raise TypeError(f'{cls} is not maintainable')

            # A reference to a MaintainableArtefact that is not (yet) defined
            # in the current message is, necessarily, external, so finding
            # is_external_reference=False in the kwargs is a fatal error here.
            assert kwargs.setdefault('is_external_reference', True)

            # Create a new object and add to index
            self._index[key] = cls(id=id, **kwargs)

        # Existing or newly-created object
        return self._index[key]

    def _named(self, cls, elem, **kwargs):
        """Parse a NameableArtefact of *cls* from *elem*.

        NameableArtefacts may have .name and .description attributes that are
        InternationalStrings, plus zero or more Annotations. _named() handles
        these common elements, and returns an object and a _parse()'d dict of
        other, class-specific child values.

        Additional *kwargs* are used when parsing the children of *elem*.
        """
        # Apply conversions to attributes
        convert_attrs = {
            'agency_id': ('maintainer', lambda value: Agency(id=value)),
            'role': ('role', lambda value:
                     ConstraintRole(role=ConstraintRoleType[value])),
            }

        attr = {}
        for name, value in elem.attrib.items():
            # Name in snake case
            name = to_snake(name)
            # Optional new name and function to transform the value
            (name, xform) = convert_attrs.get(name, (name, lambda v: v))
            # Store transformed value
            attr[name] = xform(value)

        try:
            # Maybe retrieve an existing reference
            obj = self._maintained(cls, **attr)
            # Since the object is now being parsed, it's defined in the current
            # message and no longer an external reference
            obj.is_external_reference = False
        except TypeError:
            # Instantiate the class and store its attributes
            obj = cls(**attr)

        # Store object for parsing children
        self._current[(cls, obj.id)] = obj

        # Parse children
        values = self._parse(elem, **kwargs)

        # Store the name, description and annotations
        add_localizations(obj.name, values.pop('name'))
        add_localizations(obj.description, values.pop('description', []))
        obj.annotations = wrap(values.pop('annotations', []))

        # Return the instance and any non-name values
        return obj, values

    def _get_current(self, cls, id=None):
        """Return an instance of *cls* in the :attr:`_current` scope.

        *cls* may be a single class or tuple of classes valid as the
        `classinfo` argument of :func:`issubclass`. If `id` is given, the
        object must also have a matching ID.

        Raises RuntimeError if there are 0, or 2 or more instances.
        """
        results = []
        for k, obj in self._current.items():
            if issubclass(k[0], cls) and (id is None or id == k[1]):
                results.append(obj)

        if len(results) == 1:
            return results[0]
        elif len(results) > 1:  # pragma: no cover
            raise RuntimeError(f'cannot disambiguate multiple {cls.__name__} '
                               f'in the current scope: {results}')
        else:  # pragma: no cover
            raise RuntimeError(f'no {cls.__name__} in the current scope')

    def _clear_current(self, scope):
        """Clear references from self._current at the end of *scope*."""
        classes = {
            'CategoryScheme': (Category, CategoryScheme),
            'Categorisation': (Categorisation,),
            'Codelist': (Code,),
            'ConceptScheme': (Concept, ConceptScheme),
            'ContentConstraint': (ContentConstraint,),
            'Dataflow': (DataflowDefinition,),
            'DataSet': (DataStructureDefinition,),
            'DataStructure': (DataStructureDefinition,),
            }.get(scope, [])

        if len(classes) == 0:
            return

        for k in list(self._current.keys()):
            if k[0] in classes:
                self._current.pop(k)

    def _get_cc_dsd(self):
        """Return the DSD for the ContentConstraint in the current scope."""
        return list(self._get_current(ContentConstraint).content)[0].structure

    # Parsers for common elements

    def parse_international_string(self, elem):
        # Return a tuple (locale, text)
        return (elem.attrib.get(qname('xml', 'lang'), DEFAULT_LOCALE),
                elem.text)

    def parse_text(self, elem):
        return elem.text

    def parse_ref(self, elem, parent=None):
        """References to Identifiable- and MaintainableArtefacts.

        `parent` is the tag containing the reference.
        """
        # Unused attributes
        attr = copy(elem.attrib)
        attr.pop('agencyID', None)
        attr.pop('version', None)

        if elem.tag == 'URN':
            # Ref is a URN
            return self._maintained(urn=elem.text)

        # Every non-URN ref has an 'id' attribute
        ref_id = attr.pop('id')

        # Determine the class of the ref'd object
        try:
            # 'package' and 'class' attributes give the class directly
            cls = get_class(attr.pop('package'), attr.pop('class'))
        except KeyError:
            # No 'package' and 'class' attributes

            if parent == 'Parent':
                # Ref to parent of an Item in an ItemScheme; the ref'd object
                # has the same class as the Item
                cls = getattr(pandasdmx.model, self._stack[-1])
            elif parent in ('AttachmentGroup', 'Group'):
                cls = GroupDimensionDescriptor
            elif parent in ('Dimension', 'DimensionReference'):
                # References to Dimensions
                cls = [Dimension, TimeDimension]
            else:
                cls = getattr(pandasdmx.model, parent)

        # Get or instantiate the object itself
        try:
            # Some refs to IdentifiableArtefacts specify the parent
            # MaintainableArtefact

            # Attributes of the maintainable parent; this raises KeyError if
            # not present
            parent_attrs = dict(id=attr.pop('maintainableParentID'),
                                version=attr.pop('maintainableParentVersion'))
            assert len(attr) == 0

            # Class of the maintainable parent object
            parent_cls = {
                Category: CategoryScheme,
                Code: Codelist,
                Concept: ConceptScheme,
                DataProvider: DataProviderScheme,
                }[cls]

            # Retrieve or create the parent
            parent = self._maintained(parent_cls, **parent_attrs)

            # Retrieve or create the referenced object within the parent
            return parent.setdefault(id=ref_id, **attr)
        except KeyError:
            pass

        # Instantiate a new MaintainableArtefact
        try:
            return self._maintained(cls, id=ref_id)
        except TypeError:
            # 'cls' is not a MaintainableArtefact
            pass

        # Look up an existing IdentifiableArtefact in the current scope
        for cls in wrap(cls):
            try:
                return self._current[(cls, ref_id)]
            except KeyError:
                pass

        # Failed; probably a forward reference
        raise Reparse(0)

    # Parsers for elements appearing in data messages

    def parse_attributes(self, elem):
        result = {}

        ad = self._get_current(AttributeDescriptor)
        for e in elem.iterchildren():
            da = ad.get(e.attrib['id'])
            av = AttributeValue(value=e.attrib['value'], value_for=da)
            result[da.id] = av
        return result

    def parse_header(self, elem):
        # Collect values from *elem* and its children using XPath
        values = {}
        for key, xpath in HEADER_XPATH.items():
            matches = xpath(elem)
            if len(matches) == 0:
                continue
            values[key] = matches[0] if len(matches) == 1 else matches

        # Handle a reference to a DataStructureDefinition
        attrs = {}
        for k in ['id', 'agencyid', 'version', 'urn']:
            value = values.pop('structure_ref_' + k, None)
            if not value:
                continue
            elif k == 'agencyid':
                attrs['maintainer'] = Agency(id=value)
            else:
                attrs[k] = value

        if set(attrs.keys()) == {'urn'}:
            attrs['id'] = values['structure_id']

        extra = []

        if 'id' in attrs:
            # Create or retrieve the DSD. NB if the dsd argument was provided
            # to read_message(), this should be the same DSD
            dsd = self._maintained(DataStructureDefinition, **attrs)

            if 'structure_id' in values:
                # Add the DSD to the index a second time, using the message
                # -specific structure ID (rather that the DSD's own ID).
                key = ('DataStructureDefinition', values['structure_id'])
                self._index[key] = dsd

            # Create a DataflowDefinition
            dfd = DataflowDefinition(id=values.pop('structure_id'),
                                     structure=dsd)
            extra.append(dfd)

            # Store the observation at dimension level
            dim_at_obs = values.pop('dim_at_obs')
            if dim_at_obs == 'AllDimensions':
                self._obs_dim = AllDimensions
            else:
                # Retrieve or create the Dimension
                args = dict(id=dim_at_obs, order=1e9)
                if 'TimeSeries' in self._stack[0]:
                    # {,StructureSpecific}TimeSeriesData message → the
                    # dimension at observation level is a TimeDimension
                    args['cls'] = TimeDimension
                self._obs_dim = dsd.dimensions.get(**args)

        # Maybe return the DFD; see .initialize()
        return [Header(**values)] + extra

    def parse_message(self, elem):
        f = Footer(**elem.attrib)
        for locale, label in self._parse(elem)['text']:
            f.text.append(InternationalString(**{locale: label}))
        return f

    def parse_dataset(self, elem):
        # Attributes: structure reference to a DSD
        for attr in ['structureRef', qname('data', 'structureRef')]:
            if attr in elem.attrib:
                structure_ref = elem.attrib[attr]
                break

        # Create or retrieve (structure-specific message) the DSD
        dsd = self._maintained(DataStructureDefinition, structure_ref)
        # Add DSD contents to the indices for use in recursive parsing
        self._add_to_index(indexables_from_dsd(dsd))
        self._current[(DataStructureDefinition, None)] = dsd

        # DataSet class, e.g. GenericDataSet for root XML tag 'GenericData'
        DataSetClass = getattr(pandasdmx.model, f'{self._stack[0]}Set')

        # Create the object
        ds = DataSetClass(structured_by=dsd)

        values = self._parse(elem, unwrap=False)

        # Process groups
        ds.group = {g: [] for g in values.pop('group', [])}

        # Process series
        for series_key, obs_list in values.pop('series', []):
            # Add observations under this key
            ds.add_obs(obs_list, series_key)

        # Process bare observations
        ds.add_obs(values.pop('obs', []))

        assert len(values) == 0
        return ds

    def parse_group(self, elem):
        """<generic:Group>, <structure:Group>, or <Group>."""
        values = self._parse(elem)

        # Check which namespace this Group tag is part of
        if elem.tag == qname('gen', 'Group'):
            # generic → GroupKey in a DataMessage
            gk = values.pop('groupkey')
            gk.attrib.update(values.pop('attributes', {}))
            result = gk
        elif elem.tag == qname('str', 'Group'):
            # structure → GroupDimensionDescriptor
            gdd = GroupDimensionDescriptor(
                id=elem.attrib['id'],
                components=wrap(values.pop('groupdimension')))

            # Early update of the DSD so that later definitions in the DSD can
            # reference gdd
            dsd = self._get_current(DataStructureDefinition)
            dsd.group_dimensions[gdd.id] = gdd

            result = gdd
        else:
            # no namespace → GroupKey in a StructureSpecificData message
            dsd = self._get_current(DataStructureDefinition)

            # Pop the 'type' attribute
            args = copy(elem.attrib)
            group_id = args.pop(qname('xsi', 'type')).split(':')[-1]
            try:
                gdd = self._current[(GroupDimensionDescriptor, group_id)]
            except KeyError:
                # DSD not supplied when parsing a StructureSpecificMessage
                pass
            else:
                args['described_by'] = gdd

            result = GroupKey(**args, dsd=dsd)

        assert len(values) == 0
        return result

    def parse_key(self, elem):
        """SeriesKey, GroupKey, observation dimensions."""
        cls = {
            'GroupKey': GroupKey,
            'ObsKey': Key,
            'SeriesKey': SeriesKey,
            'Key': DataKey,  # for DataKeySet
            }[QName(elem).localname]
        if cls is not DataKey:
            # Most data: the value is specified as an XML attribute
            kv = {e.attrib['id']: e.attrib['value'] for e in
                  elem.iterchildren()}

            return cls(**kv, dsd=self._get_current(DataStructureDefinition))
        else:
            # <str:DataKeySet> and <str:CubeRegion>: the value(s) are specified
            # with a <com:Value>...</com:Value> element.
            kvs = {}
            for e in elem.iterchildren():
                c = self._get_cc_dsd().dimensions.get(e.attrib['id'])
                kvs[c] = ComponentValue(value_for=c,
                                        value=self._parse(e)['value'])
            return cls(included=elem.attrib.get('isIncluded', True),
                       key_value=kvs)

    def parse_obs(self, elem):
        values = self._parse(elem)

        dsd = self._get_current(DataStructureDefinition)

        # Attached attributes
        aa = values.pop('attributes', {})

        if 'obskey' in values:
            key = values.pop('obskey')
        elif 'obsdimension' in values:
            od = values.pop('obsdimension')
            dim = self._obs_dim.id
            if len(od) == 2:
                assert od['id'] == dim, (values, dim)
            key = Key(**{dim: od['value']}, dsd=dsd)

        if len(values):
            value = values.pop('obsvalue', None)
        else:
            # StructureSpecificData message—all information stored as XML
            # attributes of the <Observation>.
            attr = copy(elem.attrib)

            # Value of the observation
            value = attr.pop('OBS_VALUE', None)

            # Use the DSD to separate dimensions and attributes
            key = Key(**attr, dsd=dsd)

            # Remove attributes from the Key to be attached to the Observation
            aa.update(key.attrib)
            key.attrib = {}

        assert len(values) == 0, values
        return Observation(dimension=key, value=value, attached_attribute=aa)

    def parse_obsdimension(self, elem):
        assert set(elem.attrib.keys()) <= {'id', 'value'}
        return copy(elem.attrib)

    def parse_obsvalue(self, elem):
        assert len(elem.attrib) == 1, elem.attrib
        return elem.attrib['value']

    def parse_series(self, elem):
        values = self._parse(elem)
        try:
            series_key = values.pop('serieskey')
            series_key.attrib.update(values.pop('attributes', {}))
        except KeyError:
            # StructureSpecificData message
            dsd = self._get_current(DataStructureDefinition)
            series_key = SeriesKey(**elem.attrib, dsd=dsd)
        obs_list = wrap(values.pop('obs', []))
        for o in obs_list:
            o.series_key = series_key
        assert len(values) == 0
        return (series_key, obs_list)

    # Parsers for elements appearing in structure messages

    def parse_structures(self, elem):
        return self._parse(elem, unwrap=False)

    def parse_organisation(self, elem):
        cls = getattr(pandasdmx.model, QName(elem).localname)
        o, values = self._named(cls, elem)
        o.contact = wrap(values.pop('contact', []))
        assert len(values) == 0
        return o

    def parse_contact(self, elem):
        values = self._parse(elem, unwrap=False)
        # Map XML element names to the class attributes in the SDMX-IM spec
        values['name'] = values.pop('name')[0]
        values['telephone'] = values.pop('telephone', [None])[0]
        values['org_unit'] = values.pop('department', [{}])[0]
        values['responsibility'] = values.pop('role', [{}])[0]
        return Contact(**values)

    def parse_annotation(self, elem):
        values = self._parse(elem)

        # Rename values from child elements: 'annotationurl' → 'url'
        for tag in ('text', 'title', 'type', 'url'):
            try:
                values[tag] = values.pop('annotation' + tag)
            except KeyError:
                pass

        # Optional 'id' attribute
        try:
            values['id'] = elem.attrib['id']
        except KeyError:
            pass

        return Annotation(**values)

    def parse_code(self, elem):
        c, values = self._named(Code, elem)
        try:
            c.parent = values.pop('parent')
            c.parent.child.append(c)
        except KeyError:
            pass
        assert len(values) == 0, values
        return c

    def parse_categorisation(self, elem):
        c, values = self._named(Categorisation, elem)
        c.artefact = values.pop('source')
        c.category = values.pop('target')
        assert len(values) == 0
        return c

    def parse_category(self, elem):
        c, values = self._named(Category, elem, unwrap=False)
        for child_category in values.pop('category', []):
            c.child.append(child_category)
            child_category.parent = c
        assert len(values) == 0
        return c

    def parse_categoryscheme(self, elem):
        cs, values = self._named(CategoryScheme, elem)
        cs.extend(values.pop('category', []))
        assert len(values) == 0
        return cs

    def parse_codelist(self, elem):
        cl, values = self._named(Codelist, elem, unwrap=False)
        cl.extend(values.pop('code', []))
        assert len(values) == 0
        return cl

    def parse_concept(self, elem):
        c, values = self._named(Concept, elem)
        c.core_representation = values.pop('corerepresentation', None)
        try:
            c.parent = values.pop('parent')
        except KeyError:
            pass
        assert len(values) == 0
        return c

    def parse_conceptidentity(self, elem):
        # <ConceptIdentity> element can contain a child <URN>. Unlike other
        # URNs, this references a non-maintainable class (Concept), rather than
        # its maintainable parent (ConceptScheme); so parse_ref fails.

        # Parse children, which should only be a <URN>
        values = self._parse(elem)
        if set(values.keys()) != {'urn'}:
            raise ValueError(values)

        # URN should refer to a Concept
        match = URN.match(values['urn']).groupdict()
        if match['class'] != 'Concept':
            raise ValueError(values['urn'])

        # Look up the parent ConceptScheme
        cls = get_class(match['package'], 'ConceptScheme')
        cs = self._maintained(cls=cls, id=match['id'])

        # Get or create the Concept within *cs*
        return cs.setdefault(id=match['item_id'])

    def parse_constraintattachment(self, elem):
        constrainables = self._parse(elem)
        assert len(constrainables) == 1
        result = list(constrainables.values())[0]

        # Also add to the parent ContentConstraint for use in parsing KeyValues
        self._get_current(ContentConstraint).content.add(result)

        return result

    def parse_orgscheme(self, elem):
        cls = getattr(pandasdmx.model, QName(elem).localname)
        os, values = self._named(cls, elem, unwrap=False)
        # Get the list of organisations. The following assumes that the
        # *values* dict has only one item. Otherwise, the returned item will be
        # unpredictable.
        # TODO review the code parsing the children to verify that the
        #      assumption always holds.
        _, orgs = values.popitem()
        os.extend(orgs)
        return os

    def parse_conceptscheme(self, elem):
        cs, values = self._named(ConceptScheme, elem, unwrap=False)
        cs.extend(values.pop('concept', []))
        assert len(values) == 0
        return cs

    def parse_dataflow(self, elem):
        dfd, values = self._named(DataflowDefinition, elem)
        dfd.structure = values.pop('structure')
        assert len(values) == 0
        return dfd

    def parse_datastructure(self, elem):
        dsd, values = self._named(DataStructureDefinition, elem)
        target = {
            DimensionDescriptor: 'dimensions',
            AttributeDescriptor: 'attributes',
            MeasureDescriptor: 'measures',
            GroupDimensionDescriptor: 'group_dimensions',
            }
        for c in values.pop('datastructurecomponents'):
            attr = target[type(c)]

            if attr == 'group_dimensions':
                # These are already added 'eagerly', by parse_group
                continue

            setattr(dsd, attr, c)

        assert len(values) == 0
        return dsd

    def parse_componentlist(self, elem):
        attr = copy(elem.attrib)

        # Determine the class
        try:
            cls_name = attr.pop('id')
        except KeyError:
            # SDMX-ML spec for, e.g. DimensionList: "The id attribute is
            # provided in this case for completeness. However, its value is
            # fixed to 'DimensionDescriptor'."
            cls_name = QName(elem).localname.replace('List', 'Descriptor')
        finally:
            ComponentListClass = getattr(pandasdmx.model, cls_name)

        cl = ComponentListClass(
            components=list(chain(*self._parse(elem, unwrap=False).values())),
            **attr,
        )

        try:
            cl.assign_order()
        except AttributeError:
            pass

        return cl

    def parse_dimension(self, elem):
        values = self._parse(elem)

        # Object class: Dimension, MeasureDimension, or TimeDimension
        DimensionClass = getattr(pandasdmx.model, QName(elem).localname)

        args = copy(elem.attrib)
        try:
            args['order'] = int(args.pop('position'))
        except KeyError:
            pass

        args.update(dict(
            concept_identity=values.pop('conceptidentity'),
            local_representation=values.pop('localrepresentation', None),
        ))
        assert len(values) == 0, values

        return DimensionClass(**args)

    def parse_groupdimension(self, elem):
        values = self._parse(elem)
        d = values.pop('dimensionreference')
        assert len(values) == 0
        return d

    def parse_attribute(self, elem):
        if self._stack[-1] == 'CubeRegion':
            # <com:Attribute> inside a CubeRegion is a MemberSelection
            return self.parse_memberselection(elem)

        args = dict(id=elem.attrib['id'])
        try:
            args['urn'] = elem.attrib['urn']
        except KeyError:
            pass

        try:
            us = elem.attrib['assignmentStatus']
        except KeyError:
            pass
        else:
            args['usage_status'] = UsageStatus[us.lower()]

        values = self._parse(elem)
        args.update(dict(
            concept_identity=values.pop('conceptidentity'),
            local_representation=values.pop('localrepresentation', None),
            related_to=values.pop('attributerelationship'),
        ))
        assert len(values) == 0

        return DataAttribute(**args)

    def parse_primarymeasure(self, elem):
        values = self._parse(elem)
        pm = PrimaryMeasure(
            concept_identity=values.pop('conceptidentity'),
            local_representation=values.pop('localrepresentation', None),
            **elem.attrib,
            )
        assert len(values) == 0
        return pm

    def parse_attributerelationship(self, elem):
        # Child element names
        tags = set([QName(e).localname for e in elem.iterchildren()])

        if 'PrimaryMeasure' not in tags:
            # Avoid recurive _parse() here, because it may contain a Ref to
            # a PrimaryMeasure that is not yet defined
            values = self._parse(elem, unwrap=False)
        else:
            values = []

        args = {}
        try:
            tags.remove('AttachmentGroup')
        except KeyError:
            pass
        else:
            args['group_key'] = values.pop('attachmentgroup')[0]

        tag = tags.pop()
        assert len(tags) == 0, tags

        cls = {
            'Dimension': DimensionRelationship,
            'PrimaryMeasure': PrimaryMeasureRelationship,
            'None': NoSpecifiedRelationship,
            'Group': DimensionRelationship,
        }[tag]

        if tag == 'Dimension':
            args['dimensions'] = values.pop('dimension')
        elif tag == 'Group':
            # Reference to a GroupDimensionDescriptor
            args['group_key'] = values.pop('group')[0]
        elif tag == 'None':
            values.pop('none')
        assert len(values) == 0, values

        return cls(**args)

    def parse_representation(self, elem):
        r = Representation()
        values = self._parse(elem, unwrap=False)
        if 'enumeration' in values:
            for e in values.pop('enumeration'):
                if isinstance(e, str):
                    e = ItemScheme(urn=e)
                r.enumerated = e
            if 'enumerationformat' in values:
                r.non_enumerated = values.pop('enumerationformat')
        elif 'textformat' in values:
            r.non_enumerated = values.pop('textformat')

        assert len(values) == 0
        return r

    def parse_facet(self, elem):
        # Parse facet value type; SDMX-ML default is 'String'
        fvt = elem.attrib.get('textType', 'String')
        # Convert case of the value. In XML, first letter is uppercase; in
        # the spec and Python enum, lowercase.
        f = Facet(value_type=FacetValueType[fvt[0].lower() + fvt[1:]])

        # Other attributes are for Facet.type, an instance of FacetType
        for key, value in elem.attrib.items():
            if key == 'textType':
                continue
            # Convert attribute name from camelCase to snake_case
            setattr(f.type, to_snake(key), value)

        return f

    # Parsers for constraints etc.
    def parse_contentconstraint(self, elem):
        role = elem.attrib.pop('type').lower()
        elem.attrib['role'] = 'allowable' if role == 'allowed' else role
        cc, values = self._named(ContentConstraint, elem)
        cc.content.update(wrap(values.pop('constraintattachment')))
        cc.data_content_region.append(values.pop('cuberegion', None))
        cc.data_content_keys = values.pop('datakeyset', None)
        assert len(values) == 0, values
        return cc

    def parse_cuberegion(self, elem):
        values = self._parse(elem, unwrap=False)
        cr = CubeRegion(included=elem.attrib['include'])

        # Combine member selections for Dimensions and Attributes
        for ms in values.pop('keyvalue', []) + values.pop('attribute', []):
            cr.member[ms.values_for] = ms

        assert len(values) == 0
        return cr

    def parse_memberselection(self, elem):
        """<com:KeyValue> (not inside <com:Key>); or <com:Attribute>."""
        values = self._parse(elem)
        values = list(map(lambda v: MemberValue(value=v), values['value']))

        # Values are for either a Dimension or Attribute, based on tag name
        kind = {
            'KeyValue': ('dimensions', Dimension),
            'Attribute': ('attributes', DataAttribute),
        }.get(QName(elem).localname)

        try:
            # Navigate from the current ContentConstraint to a
            # ConstrainableArtefact. If this is a DataFlow, it has a DSD.
            dsd = self._get_cc_dsd()
        except AttributeError:
            # Failed because the ContentConstraint is attached to something,
            # e.g. DataProvider, that does not provide an association to a DSD.
            # Try to get a Component from the current scope with matching ID.
            component = self._get_current(cls=kind[1], id=elem.attrib['id'])
        else:
            # Get the Component from the correct list according to the kind
            component = getattr(dsd, kind[0]).get(elem.attrib['id'])

        return MemberSelection(values=values, values_for=component)

    def parse_datakeyset(self, elem):
        values = self._parse(elem)
        dks = DataKeySet(included=elem.attrib.pop('isIncluded'),
                         keys=values.pop('key'))
        assert len(values) == 0
        return dks

    def parse_provisionagreement(self, elem):
        pa, values = self._named(ProvisionAgreement, elem)
        pa.structure_usage = values.pop('structureusage')
        pa.data_provider = values.pop('dataprovider')
        assert len(values) == 0, values
        return pa

    # Parsers for elements appearing in error messages

    def parse_errormessage(self, elem):
        values = self._parse(elem)
        values['text'] = [InternationalString(values['text'])]
        values['code'] = elem.attrib['code']
        return values


def indexables_from_dsd(dsd):
    """Return indexable items from a DSD."""
    # AttributeDescriptor and DataAttributes
    yield dsd.attributes
    yield from dsd.attributes.components

    # DimensionDescriptor and *Dimensions
    yield dsd.dimensions
    yield from dsd.dimensions.components

    if dsd.measures:
        yield dsd.measures
        yield from dsd.measures.components

    for gdd in dsd.group_dimensions.values():
        yield gdd
        yield from gdd.components
