"""SDMXML v2.1 reader"""
from collections import defaultdict
from copy import copy
from inspect import isclass
from itertools import chain
import re

from lxml import etree
from lxml.etree import QName, XPath

from pandasdmx.exceptions import ParseError, XMLParseError
from pandasdmx.message import (
    DataMessage,
    ErrorMessage,
    Footer,
    Header,
    StructureMessage,
    )
from pandasdmx.model import (
    DEFAULT_LOCALE,
    Agency,
    AgencyScheme,
    AllDimensions,
    Annotation,
    AttributeDescriptor,
    NoSpecifiedRelationship,
    PrimaryMeasureRelationship,
    DimensionRelationship,
    AttributeValue,
    Categorisation,
    Category,
    CategoryScheme,
    Code,
    Codelist,
    ComponentValue,
    Concept,
    ConceptScheme,
    Contact,
    ContentConstraint,
    ConstraintRole,
    ConstraintRoleType,
    CubeRegion,
    DataAttribute,
    DataflowDefinition,
    DataKey,
    DataKeySet,
    DataProvider,
    DataProviderScheme,
    DataSet,
    DataStructureDefinition,
    Dimension,
    DimensionDescriptor,
    Facet,
    FacetValueType,
    GroupDimensionDescriptor,
    GroupKey,
    IdentifiableArtefact,
    InternationalString,
    ItemScheme,
    MaintainableArtefact,
    MeasureDescriptor,
    MemberSelection,
    MemberValue,
    Key,
    KeyValue,
    Observation,
    PrimaryMeasure,
    ProvisionAgreement,
    Representation,
    SeriesKey,
    TimeDimension,
    UsageStatus,
    )

from pandasdmx.reader import BaseReader


# Regular expression for URNs used as references
URN = re.compile(r'urn:sdmx:org\.sdmx\.infomodel'
                 r'\.(?P<package>[^\.]*)'
                 r'\.(?P<class>[^=]*)=((?P<agency>[^:]*):)?'
                 r'(?P<id>[^\(]*)(\((?P<version>\d*)\))?')


# XML namespaces
NS = {
    'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
    'data': ('http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/'
             'structurespecific'),
    'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
    'mes': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
    'gen': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
    'footer':
        'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message/footer',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }


def qname(ns, name):
    """Return a fully-qualified tag *name* in namespace *ns*."""
    return QName(NS[ns], name)


# Mapping tag names → Message classes
MESSAGE = {qname('mes', name): cls for name, cls in (
    ('Structure', StructureMessage),
    ('GenericData', DataMessage),
    ('GenericTimeSeriesData', DataMessage),
    ('StructureSpecificData', DataMessage),
    ('StructureSpecificTimeSeriesData', DataMessage),
    ('Error', ErrorMessage),
    )}


# XPath expressions for reader._collect()
COLLECT = {
    'header': {
        'id': 'mes:ID/text()',
        'prepared': 'mes:Prepared/text()',
        'sender': 'mes:Sender/@*',
        'receiver': 'mes:Receiver/@*',
        'structure_id': 'mes:Structure/@structureID',
        'dim_at_obs': 'mes:Structure/@dimensionAtObservation',
        'structure_ref_id':
            # 'Structure' vs 'StructureUsage' varies across XML specimens.
            ('(mes:Structure/com:Structure/Ref/@id | '
             'mes:Structure/com:StructureUsage/Ref/@id)[1]'),
        'structure_ref_agencyid':
            ('(mes:Structure/com:Structure/Ref/@agencyID | '
             'mes:Structure/com:StructureUsage/Ref/@agencyID)[1]'),
        'structure_ref_version':
            ('(mes:Structure/com:Structure/Ref/@version | '
             'mes:Structure/com:StructureUsage/Ref/@version)[1]'),
        'structure_ref_urn': 'mes:Structure/com:Structure/URN/text()',
        },
    'obs': {
        'dimension': 'gen:ObsDimension/@value',
        'value': 'gen:ObsValue/@value',
        'attribs': 'gen:Attributes',
        },
    }

# Precompile paths
for group, vals in COLLECT.items():
    for key, path in vals.items():
        COLLECT[group][key] = XPath(path, namespaces=NS, smart_strings=False)


# For Reader._parse(): tag name → Reader.parse_[…] method to use
METHOD = {
    'AnnotationText': 'international_string',
    'Name': 'international_string',
    'Department': 'international_string',
    'Description': 'international_string',
    'Role': 'international_string',
    'Text': 'international_string',

    'DimensionList': 'grouping',
    'AttributeList': 'grouping',
    'MeasureList': 'grouping',

    'CoreRepresentation': 'representation',
    'LocalRepresentation': 'representation',

    'AnnotationType': 'text',
    'AnnotationTitle': 'text',
    'AnnotationURL': 'text',
    'Email': 'text',
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

    'TextFormat': 'facet',
    'EnumerationFormat': 'facet',

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
    'DimensionReference': 'ref',
    'Parent': 'ref',
    'Source': 'ref',
    'Structure': 'ref',  # str:Structure, not mes:Structure
    'Target': 'ref',
    'ConceptIdentity': 'ref',
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
    'registry': {ContentConstraint},
    }


def get_class(package, cls):
    """Return a class object for string *cls* and *package* names."""
    if isinstance(cls, str):
        if cls in 'Dataflow DataStructure':
            cls += 'Definition'
        cls = globals()[cls]

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


class Reader(BaseReader):
    """Read SDMX-ML 2.1 and expose it as instances from :mod:`pandasdmx.model`.

    The implementation is recursive, and depends on:

    - :meth:`_parse`, :meth:`_collect`, :meth:`_named` and :meth:`_maintained`.
    - State variables :attr:`_current`, :attr:`_stack, :attr:`_index`.
    """
    # TODO subclass the main reader for StructureSpecific*Data messages to
    #      avoid branching

    # State variables for reader

    # Stack (0 = top) of tag names being parsed by _parse().
    # Tag parsers may examine the stack to determine context for parsing.
    _stack = []

    # Map of (class name, id) → pandasdmx.model object.
    # Only IdentifiableArtefacts should be stored. See _maintained().
    _index = {}

    # Similar to _index, but specific to the current scope.
    _current = {}

    def read_message(self, source):
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

    def _collect(self, group, elem):
        """Collect values from *elem* and its children using XPaths in *group*.

        A dictionary is returned.
        """
        result = {}
        for key, xpath in COLLECT[group].items():
            matches = xpath(elem)
            if len(matches) == 0:
                continue
            result[key] = matches[0] if len(matches) == 1 else matches
        return result

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

            # Add objects with IDs to the appropriate index
            for r in result:
                if isinstance(r, MaintainableArtefact) and not \
                        r.is_external_reference:
                    # Global index for MaintainableArtefacts
                    self._index[(r.__class__.__name__, r.id)] = r
                elif isinstance(r, IdentifiableArtefact):
                    # Current scope index for IdentifiableArtefacts
                    self._current[(r.__class__, r.id)] = r

            # Store the parsed elements
            results[tag_name.lower()].extend(result)

        # Restore state
        self._clear_current(self._stack.pop())

        if unwrap:
            # Unwrap every value in results that is a length-1 list
            results = {k: v[0] if len(v) == 1 else v for k, v in
                       results.items()}

        return results

    def _maintained(self, cls=None, id=None, urn=None, match_subclass=False,
                    **kwargs):
        """Retrieve or instantiate a MaintainableArtefact of *cls* with *ids.

        If the object has been parsed (i.e. is in :attr:`_index`), it is
        returned; if not and `match_subclass` is :obj:`False`, it is
        instantiated with ``is_external_reference=True``, passing `kwargs`.

        If *urn* is given, it is used to determine *cls* and *id*, per the URN
        regular expression.

        If *match_subclass* is False, *cls* may either be a string or a class
        for a subclass of MaintainableArtefact. If *match_subclass* is True,
        *cls* must be a class.
        """
        if urn:
            match = URN.match(urn).groupdict()
            cls = get_class(match['package'], match['class'])
            id = match['id']

        if match_subclass:
            for key, obj in self._index.items():
                if isinstance(obj, cls) and obj.id == id:
                    return obj
            raise ValueError(cls, id)

        key = (cls.__name__, id) if isclass(cls) else (cls, id)

        # Maybe create a new object
        if key not in self._index:
            if not isclass(cls):
                raise TypeError(f'cannot instantiate from {cls!r}')
            elif not issubclass(cls, MaintainableArtefact):
                raise TypeError(f'{cls} is not maintainable')

            # Create a new object. A reference to a MaintainableArtefact that
            # is not defined in the current message is, necessarily, external
            assert kwargs.pop('is_external_reference', True)
            self._index[key] = cls(id=id, is_external_reference=True,
                                   **kwargs)

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
            'agencyID': ('maintainer', lambda value: Agency(id=value)),
            'isExternalReference': ('is_external_reference', bool),
            'isFinal': ('is_final', bool),
            'isPartial': ('is_partial', bool),
            'structureURL': ('structure_url', lambda value: value),
            'role': ('role', lambda value:
                     ConstraintRole(role=ConstraintRoleType[value])),
            'validFrom': ('valid_from', str),
            'validTo': ('valid_to', str),
            }

        attr = copy(elem.attrib)
        for source, (target, xform) in convert_attrs.items():
            try:
                attr[target] = xform(attr.pop(source))
            except KeyError:
                continue

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

    def _set_obs_dim(self, value):
        """Store the observation dimension for the current DataSet."""
        if value == 'AllDimensions':
            self._obs_dim = AllDimensions
        else:
            try:
                # Retrieve an already-defined Dimension (e.g. from the DSD)
                obs_dim = self._index[('Dimension', value)]
            except KeyError:
                obs_dim = Dimension(id=value)
            self._obs_dim = wrap(obs_dim)

    def _get_current(self, cls):
        """Return the sole instance of *cls* in the :attr:`_current` scope.

        Raises AssertionError if there are 0, or 2 or more instances.
        """
        results = []
        for k, obj in self._current.items():
            if k[0] is cls:
                results.append(obj)

        assert len(results) == 1
        return results[0]

    def _clear_current(self, scope):
        """Clear references from self._current at the end of *scope*."""
        classes = {
            'CategoryScheme': (Category, CategoryScheme),
            'Categorisation': (Categorisation,),
            'Codelist': (Code,),
            'ConceptScheme': (Concept, ConceptScheme),
            'ContentConstraint': (ContentConstraint,),
            'Dataflow': (DataflowDefinition,),
            'DataStructure': (DataStructureDefinition,),
            }.get(scope, [])

        if len(classes) == 0:
            return

        for k in list(self._current.keys()):
            if k[0] in classes:
                self._current.pop(k)

    def _get_cc_dimension(self, id):
        """Return a Dimension for *id* in the current scope.

        Navigates from a ContentConstraint in self._current, to its Dataflow,
        DataStructureDefinition, and DimensionDescriptor.
        """
        return list(self._get_current(ContentConstraint).content)[0] \
            .structure.dimensions.get(id)

    # Parsers for common elements

    def parse_international_string(self, elem):
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
                cls = globals()[self._stack[-1]]
            elif parent == 'Group':
                cls = GroupDimensionDescriptor
            elif parent in ('Dimension', 'DimensionReference'):
                # References to Dimensions
                cls = [Dimension, TimeDimension]
            else:
                cls = globals()[parent]

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
        for e in elem.iterchildren():
            da = DataAttribute(id=e.attrib['id'])
            av = AttributeValue(value_for=da, value=e.attrib['value'])
            result[da.id] = av
        return result

    def parse_header(self, elem):
        values = self._collect('header', elem)

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

        if 'id' in attrs:
            # Create the DSD and DFD
            dsd = self._maintained(DataStructureDefinition, **attrs)
            dfd = DataflowDefinition(id=values.pop('structure_id'),
                                     structure=dsd)

            # Also store the dimension at observation
            self._set_obs_dim(values.pop('dim_at_obs'))
            extra = [dfd]
        else:
            extra = []

        # Maybe return the DFD; see .initialize()
        return [Header(**values)] + extra

    def parse_message(self, elem):
        f = Footer(**elem.attrib)
        for locale, label in self._parse(elem)['text']:
            f.text.append(InternationalString(**{locale: label}))
        return f

    def parse_dataset(self, elem):
        values = self._parse(elem, unwrap=False)
        # Store groups
        ds = DataSet(group={g: [] for g in values.pop('group', [])})

        # Attributes
        for attr in ['structureRef', qname('data', 'structureRef')]:
            if attr in elem.attrib:
                structure_ref = elem.attrib[attr]
                break
        ds.structured_by = self._maintained(DataStructureDefinition,
                                            structure_ref)

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
            dsd.group_dimensions = gdd

            result = gdd
        else:
            # no namespace → GroupKey in a StructureSpecificData message

            # commented: destructive
            # # Discard XML Schema attribute
            # elem.attrib.pop(qname('xsi', 'type'))

            # the 'TITLE' XML attribute is an SDMX Attribute
            attrib = {}
            try:
                da = DataAttribute(id='TITLE')
                av = AttributeValue(value=elem.attrib['TITLE'], value_for=da)
                attrib[da.id] = av
            except KeyError:
                pass

            # Remaining attributes are the KeyValues
            result = GroupKey(**elem.attrib, attrib=attrib)

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
            return cls(**kv)
        else:
            # <str:DataKeySet> and <str:CubeRegion>: the value(s) are specified
            # with a <com:Value>...</com:Value> element.
            kvs = {}
            for e in elem.iterchildren():
                c = self._get_cc_dimension(e.attrib['id'])
                kvs[c] = ComponentValue(value_for=c,
                                        value=self._parse(e)['value'])
            return cls(included=elem.attrib.get('isIncluded', True),
                       key_value=kvs)

    def parse_obs(self, elem):
        # TODO handle key-values as attribs
        values = self._parse(elem)
        if len(values):
            key = (values['obskey'] if 'obskey' in values else
                   values['obsdimension'])
            if 'obsdimension' in values:
                new_key = Key()
                new_key[key.id] = key
                key = new_key
            obs = Observation(dimension=key, value=values['obsvalue'],
                              attached_attribute=values.get('attributes', {}))
        else:
            # StructureSpecificData message
            attr = copy(elem.attrib)

            # Value of the observation
            value = attr.pop('OBS_VALUE')

            # Dimensions for the key
            if self._obs_dim is AllDimensions:
                dims = list(attr.keys())
            else:
                # Use the 'dimension at observation' specified for the message
                dims = map(lambda d: d.id, self._obs_dim)

            # Create the observation, consuming attr for the key
            obs = Observation(dimension=Key(**{d: attr.pop(d) for d in dims}),
                              value=value)

            # Remaining attr members are SDMX DataAttributes
            for id, value in attr.items():
                da = DataAttribute(id=id)
                av = AttributeValue(value_for=da, value=value)
                obs.attached_attribute[da.id] = av

        return obs

    def parse_obsdimension(self, elem):
        attr = copy(elem.attrib)
        args = dict(value=attr.pop('value'))
        args['id'] = attr.pop('id', self._obs_dim[0].id)
        assert len(attr) == 0
        return KeyValue(**args)

    def parse_obsvalue(self, elem):
        return elem.attrib['value']

    def parse_series(self, elem):
        values = self._parse(elem)
        try:
            series_key = values.pop('serieskey')
            series_key.attrib.update(values.pop('attributes', {}))
        except KeyError:
            # StructureSpecificData message; treat all attributes as dimensions
            # TODO prefetch the structure or used a prefetched structure
            series_key = SeriesKey(**elem.attrib)
        obs_list = wrap(values.pop('obs', []))
        for o in obs_list:
            o.series_key = series_key
        assert len(values) == 0
        return (series_key, obs_list)

    # Parsers for elements appearing in structure messages

    def parse_structures(self, elem):
        return self._parse(elem, unwrap=False)

    def parse_organisation(self, elem):
        cls = globals()[QName(elem).localname]
        o, values = self._named(cls, elem)
        o.contact = wrap(values.pop('contact', []))
        assert len(values) == 0
        return o

    def parse_contact(self, elem):
        values = self._parse(elem, unwrap=False)
        # Map XML element names to the class attributes in the SDMX-IM spec
        values['name'] = values.pop('name')[0]
        values['telephone'] = values.pop('telephone', [None])[0]
        values['org_unit'] = values.pop('department')[0]
        values['responsibility'] = values.pop('role', [None])[0]
        return Contact(**values)

    def parse_annotation(self, elem):
        values = self._parse(elem)
        for attr in ('text', 'title', 'type', 'url'):
            try:
                values[attr] = values.pop('annotation' + attr)
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
        cs.items.extend(values.pop('category', []))
        assert len(values) == 0
        return cs

    def parse_codelist(self, elem):
        cl, values = self._named(Codelist, elem, unwrap=False)
        cl.items.extend(values.pop('code', []))
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

    def parse_constraintattachment(self, elem):
        constrainables = self._parse(elem)
        assert len(constrainables) == 1
        result = list(constrainables.values())[0]

        # Also add to the parent ContentConstraint for use in parsing KeyValues
        self._get_current(ContentConstraint).content.add(result)

        return result

    def parse_orgscheme(self, elem):
        cls = globals()[QName(elem).localname]
        os, values = self._named(cls, elem, unwrap=False)
        _, os.items = values.popitem()
        assert len(values) == 0
        return os

    def parse_conceptscheme(self, elem):
        cs, values = self._named(ConceptScheme, elem, unwrap=False)
        cs.items = values.pop('concept', [])
        assert len(values) == 0
        return cs

    def parse_dataflow(self, elem):
        dfd, values = self._named(DataflowDefinition, elem)
        dfd.structure = values.pop('structure')
        assert len(values) == 0
        return dfd

    def parse_datastructure(self, elem):
        dsd, values = self._named(DataStructureDefinition, elem)
        _target = {
            DimensionDescriptor: 'dimensions',
            AttributeDescriptor: 'attributes',
            MeasureDescriptor: 'measures',
            GroupDimensionDescriptor: 'group_dimensions',
            }
        for c in values.pop('datastructurecomponents'):
            setattr(dsd, _target[type(c)], c)

        assert len(values) == 0
        return dsd

    def parse_grouping(self, elem):
        attr = copy(elem.attrib)
        Grouping = globals()[attr.pop('id')]
        g = Grouping(**attr)
        g.components.extend(chain(*self._parse(elem, unwrap=False).values()))
        return g

    def parse_dimension(self, elem):
        values = self._parse(elem)

        # Object class: Dimension, TimeDimension, etc.
        cls = globals()[QName(elem).localname]

        attr = copy(elem.attrib)
        try:
            attr['order'] = int(attr.pop('position'))
        except KeyError:
            pass

        d = cls(
            concept_identity=values.pop('conceptidentity'),
            local_representation=values.pop('localrepresentation', None),
            **attr,
            )

        # Add to scope
        self._current[(cls, d.id)] = d

        assert len(values) == 0
        return d

    def parse_groupdimension(self, elem):
        values = self._parse(elem)
        d = values.pop('dimensionreference')
        assert len(values) == 0
        return d

    def parse_attribute(self, elem):
        attrs = {k: elem.attrib[k] for k in ('id', 'urn')}
        attrs['usage_status'] = UsageStatus[
                                       elem.attrib['assignmentStatus'].lower()]
        values = self._parse(elem)
        da = DataAttribute(
            concept_identity=values.pop('conceptidentity'),
            local_representation=values.pop('localrepresentation', None),
            related_to=values.pop('attributerelationship'),
            **attrs,
            )

        assert len(values) == 0
        return da

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
        tags = set([el.tag for el in elem.iterchildren()])
        tag = tags.pop()
        assert len(tags) == 0

        if tag == qname('str', 'Dimension'):
            values = self._parse(elem, unwrap=False)
            ar = DimensionRelationship(dimensions=values.pop('dimension'))
            assert len(values) == 0
        elif tag == qname('str', 'PrimaryMeasure'):
            # Avoid recurive _parse() here, because it may contain a Ref to
            # a PrimaryMeasure that is not yet defined
            ar = PrimaryMeasureRelationship()
        elif tag == qname('str', 'None'):
            ar = NoSpecifiedRelationship()
        elif tag == qname('str', 'Group'):
            # Reference to a GroupDimensionDescriptor
            values = self._parse(elem)
            ar = DimensionRelationship(group_key=values.pop('group'))
            assert len(values) == 0
        else:
            raise NotImplementedError(f'cannot parse {etree.tostring(elem)}')

        return ar

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
        # Convert case of the value_type. In XML, first letter is uppercase;
        # in the spec, lowercase.
        attr = copy(elem.attrib)
        value_type = attr.pop('textType', None)
        if isinstance(value_type, str):
            value_type = FacetValueType[value_type[0].lower() + value_type[1:]]
        f = Facet(value_type=value_type)
        key_map = {
            'isSequence': 'is_sequence',
            'minValue': 'min_value',
            'maxValue': 'max_value',
            'minLength': 'min_length',
            'maxLength': 'max_length',
            }
        for key, value in attr.items():
            setattr(f.type, key_map.get(key, key), value)
        return f

    # Parsers for constraints etc.
    def parse_contentconstraint(self, elem):
        # Munge

        role = elem.attrib.pop('type').lower()
        elem.attrib['role'] = 'allowable' if role == 'allowed' else role
        cc, values = self._named(ContentConstraint, elem)
        cc.content.update(wrap(values.pop('constraintattachment')))
        cc.data_content_region = values.pop('cuberegion', None)
        cc.data_content_keys = values.pop('datakeyset', None)
        assert len(values) == 0, values
        return cc

    def parse_cuberegion(self, elem):
        values = self._parse(elem)
        cr = CubeRegion(
            included=elem.attrib.pop('include'),
            member={ms.values_for: ms for ms in values.pop('keyvalue')})
        assert len(values) == 0
        return cr

    def parse_keyvalue(self, elem):
        """<com:KeyValue> NOT inside <com:Key> specifies a MemberSelection."""
        values = self._parse(elem)
        values = list(map(lambda v: MemberValue(value=v), values['value']))

        return MemberSelection(
            values=values,
            values_for=self._get_cc_dimension(elem.attrib['id']))

    def parse_datakeyset(self, elem):
        values = self._parse(elem)
        dks = DataKeySet(included=elem.attrib.pop('isIncluded'),
                         keys=values.pop('key'))
        assert len(values) == 0
        return dks

    def parse_provisionagreement(self, elem):
        return ProvisionAgreement(**self._parse(elem))

    # Parsers for elements appearing in error messages

    def parse_errormessage(self, elem):
        values = self._parse(elem)
        values['text'] = [InternationalString(values['text'])]
        values['code'] = elem.attrib['code']
        return values
