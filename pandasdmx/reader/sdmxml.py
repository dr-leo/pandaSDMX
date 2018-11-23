# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014-2016 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a reader for SDMXML v2.1.

'''
from collections import ChainMap
from inspect import isclass

from lxml import etree
from lxml.etree import QName, XPath

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
    # AttributeRelationship,
    NoSpecifiedRelationship,
    PrimaryMeasureRelationship,
    # GroupRelationship,
    DimensionRelationship,
    AttributeValue,
    Categorisation,
    Category,
    CategoryScheme,
    Code,
    Codelist,
    Concept,
    ConceptScheme,
    Contact,
    DataAttribute,
    DataflowDefinition,
    DataProvider,
    DataProviderScheme,
    DataSet,
    DataStructureDefinition,
    Dimension,
    DimensionDescriptor,
    Facet,
    GroupDimensionDescriptor,
    GroupKey,
    IdentifiableArtefact,
    InternationalString,
    ItemScheme,
    MaintainableArtefact,
    MeasureDescriptor,
    Key,
    KeyValue,
    Observation,
    PrimaryMeasure,
    Representation,
    SeriesKey,
    UsageStatus,
    )

from pandasdmx.reader import BaseReader

# XML namespaces
_ns = {
    'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
    'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
    'mes': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
    'gen': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
    'footer':
        'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message/footer',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    }


def qname(ns, name):
    """Return a fully-qualified tag *name* in namespace *ns*."""
    return QName(_ns[ns], name)


# Add namespaces
_message_class = {qname('mes', name): cls for name, cls in (
    ('Structure', StructureMessage),
    ('GenericData', DataMessage),
    ('GenericTimeSeriesData', DataMessage),
    ('Error', ErrorMessage),
    )}


# XPath expressions for reader._collect()
_collect_paths = {
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
for group, vals in _collect_paths.items():
    for key, path in vals.items():
        _collect_paths[group][key] = XPath(path, namespaces=_ns,
                                           smart_strings=False)


# For Reader._parse(): tag name → Reader.parse_[…] method to use
_parse_alias = {
    'annotationtext': 'international_string',
    'name': 'international_string',
    'department': 'international_string',
    'description': 'international_string',
    'role': 'international_string',
    'text': 'international_string',
    'dimensionlist': 'grouping',
    'attributelist': 'grouping',
    'measurelist': 'grouping',
    'corerepresentation': 'representation',
    'localrepresentation': 'representation',
    'annotationtype': 'text',
    'annotationtitle': 'text',
    'annotationurl': 'text',
    'email': 'text',
    'telephone': 'text',
    'uri': 'text',
    'urn': 'text',
    'obskey': 'key',
    'serieskey': 'key',
    'groupkey': 'key',
    'agencyscheme': 'orgscheme',
    'dataproviderscheme': 'orgscheme',
    'agency': 'organisation',
    'dataprovider': 'organisation',
    }

# Class names stored as strings in XML attributes -> pandasdmx.model classes
_parse_class = {
    'grouping': {
        'DimensionDescriptor': DimensionDescriptor,
        'AttributeDescriptor': AttributeDescriptor,
        'MeasureDescriptor': MeasureDescriptor,
        },
    'key': {
        'groupkey': GroupKey,
        'obskey': Key,
        'serieskey': SeriesKey,
        },
    'ref': {  # Keys here are concatenated 'package' and 'class' attributes
        'categoryscheme.Category': Category,
        'codelist.Codelist': Codelist,
        'conceptscheme.Concept': Concept,
        'datastructure.Dataflow': DataflowDefinition,
        'datastructure.DataStructure': DataStructureDefinition,
        },
    'ref_parent': {
        Category: CategoryScheme,
        Concept: ConceptScheme,
        },
    'orgscheme': {
        'agencyscheme': AgencyScheme,
        'dataproviderscheme': DataProviderScheme,
        },
    'organisation': {
        'agency': Agency,
        'dataprovider': DataProvider,
        },
    }

# Tag names to skip entirely
_parse_skip = [
    # Tags that are bare containers for other XML elements
    'Annotations',
    'CategorySchemes',
    'Categorisations',
    'Codelists',
    'Concepts',
    'Dataflows',
    'DataStructures',
    'DataStructureComponents',
    'Footer',
    'OrganisationSchemes',
    # Tag names that only ever contain references
    'DimensionReference',
    'Source',
    'Structure',  # str:Structure, not mes:Structure
    'Target',
    'ConceptIdentity',
    'Enumeration',
    ]


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


class ParseError(Exception):
    pass


class Reader(BaseReader):
    """Read SDMX-ML 2.1 and expose it as instances from pandasdmx.model.

    The implementation is recursive, and depends on:
    - Methods _parse(), _collect(), _named() and _maintained().
    - State variables _stack, _index.
    """
    # State variables for reader

    # Stack (0 = top) of tag names being parsed by _parse().
    # Tag parsers may examine the stack to determine context for parsing.
    _stack = []

    # Map of (class name, id) → pandasdmx.model object.
    # Only IdentifiableArtefacts should be stored. See _maintained().
    _index = {}

    def read_message(self, source):
        # Root XML element
        root = etree.parse(source).getroot()

        # Message class
        cls = _message_class[root.tag]

        # Reset state
        self._stack = [QName(root).localname.lower()]
        self._index = {}

        try:
            # Parse the tree
            values = self._parse(root)
        except Exception as e:  # pragma: no cover
            # For debugging: print the stack
            print(' > '.join(self._stack))
            if isinstance(e, ParseError):
                raise
            else:
                raise ParseError from e

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
                    ('structure', 'datastructures'),
                    ('category_scheme', 'categoryschemes'),
                    ('concept_scheme', 'concepts'),
                    ('organisation_scheme', 'organisationschemes'),
                    ):
                for obj in structures.pop(name, []):
                    getattr(msg, attr)[obj.id] = obj

            for c in structures.pop('categorisations', []):
                # Check, but do not store, the stated relationships
                assert any(c.category in cs for cs in
                           msg.category_scheme.values())
                assert c.artefact in msg.dataflow.values()

            assert len(structures) == 0

        assert len(values) == 0
        return msg

    def _collect(self, group, elem):
        """Collect values from *elem* and its children using XPaths in *group*.

        A dictionary is returned.
        """
        result = {}
        for key, xpath in _collect_paths[group].items():
            matches = xpath(elem)
            if len(matches) == 0:
                continue
            result[key] = matches[0] if len(matches) == 1 else matches
        return result

    def _parse(self, elem, rtype=dict, unwrap=True):
        """Recursively parse the XML *elem* and return pandasdmx.model objects.

        Methods like 'Reader.parse_attribute()' are called for XML elements
        with tag names like '<ns:Attribute>'; each emits pandasdmx.model
        objects.

        *rtype* controls the return type of _parse():
        - dict: a mapping of tag names to lists of objects.
        - list: a list of objects.

        If *unwrap* is True (the default), then single-entry lists are returned
        as bare objects.
        """
        # Container for results
        results = rtype()

        # Parse each child
        for child in elem:
            # Store state: tag name for the child
            tag_name = QName(child).localname.lower()
            self._stack.append(tag_name)

            # Invoke the parser for this element
            if QName(child).localname in _parse_skip:
                # Element doesn't require any parsing, per se.
                # Immediately parse its children, as a list.
                self._stack[-1] += ' (skip)'
                result = self._parse(child, rtype=list, unwrap=False)
            elif len(child) == 1 and child[0].tag == 'Ref':
                # Element contains nothing but a reference. Parse or look up
                # the reference
                result = [self.parse_ref(child[0])]
            else:
                # Parse the element, maybe using an alias
                method = 'parse_' + _parse_alias.get(tag_name, tag_name)
                result = [getattr(self, method)(child)]

            # Add objects with IDs to the index
            for r in result:
                if (isinstance(r, IdentifiableArtefact) and not
                        getattr(r, 'is_external_reference', False)):
                    self._index[(r.__class__.__name__, r.id)] = r

            # Store the result
            if rtype is dict:
                results[tag_name] = results.get(tag_name, []) + result
            else:
                results.extend(result)

            # Restore state
            self._stack.pop()

        if unwrap:
            if rtype is dict:
                # Unwrap every value in results that is a length-1 list
                results = {k: v[0] if len(v) == 1 else v for k, v in
                           results.items()}
            else:
                results = results[0] if len(results) == 1 else results

        return results

    def _maintained(self, cls, id, **kwargs):
        """Retrieve or instantiate a MaintainableArtefact of *cls*.

        *cls* may either be a string or a class. *id* is the ID of the
        MaintainableArtefact. If the object has not been parsed yet, it is
        instantiated as an external reference.
        """
        key = (cls.__name__, id) if isclass(cls) else (cls, id)

        if key not in self._index:
            if not isclass(cls):
                raise TypeError("cannot instantiate from string class name: %s"
                                % cls)
            # Create a new object. A reference to a MaintainableArtefact
            # without it being fully defined is necessarily external
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
            }

        attrs = {}
        for source, (target, xform) in convert_attrs.items():
            try:
                value = elem.attrib.pop(source)
                attrs[target] = xform(value)
            except KeyError:
                continue

        attrs = ChainMap(attrs, elem.attrib)

        if issubclass(cls, MaintainableArtefact):
            # Maybe retrieve an existing reference
            obj = self._maintained(cls, **attrs)
            # Since the object is now being parsed, it's defined in the current
            # message and no longer an external reference
            obj.is_external_reference = False
        else:
            # Instantiate the class and store its attributes
            obj = cls(**attrs)

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

    # Parsers for common elements

    def parse_international_string(self, elem):
        locale = elem.attrib.get(qname('xml', 'lang'), DEFAULT_LOCALE)
        return (locale, elem.text)

    def parse_text(self, elem):
        return elem.text

    def parse_ref(self, elem, hint=None):
        """External and internal references to MaintainableArtefacts."""
        args = {}

        # Parse attributes
        try:
            args['maintainer'] = Agency(id=elem.attrib.pop('agencyID'))
        except KeyError:
            pass
        try:
            args['version'] = elem.attrib.pop('version')
        except KeyError:
            pass

        ref_id = elem.attrib.pop('id')

        # Determine the class of the reference
        try:
            # If the element has 'package' and 'class' attributes, these give
            # the class directly
            cls_key = '.'.join([elem.attrib.pop('package'),
                                elem.attrib.pop('class')])
            cls = _parse_class['ref'][cls_key]
        except KeyError:
            cls = hint if hint else self._stack[-1].capitalize()
            if cls == 'Parent':
                # The parent of an Item in an ItemScheme has the same class as
                # the Item
                cls = self._stack[-2].capitalize()
            elif cls == 'Ref' and 'dimensionreference' in self._stack[-2]:
                return self._index[('Dimension', ref_id)]

        try:
            # Class of the maintainable parent object
            parent_cls = _parse_class['ref_parent'][cls]

            # Attributes of the maintainable parent
            parent_attrs = dict(
                id=elem.attrib.pop('maintainableParentID'),
                version=elem.attrib.pop('maintainableParentVersion'),
                )

            # Retrieve or create the parent
            parent = self._maintained(parent_cls, **parent_attrs)

            # Retrieve or create the referenced object
            obj = parent.setdefault(id=ref_id, **elem.attrib)
        except KeyError:
            # No parent object
            obj = self._maintained(cls, id=ref_id)

        assert len(elem.attrib) == 0
        return obj

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
        ds.structured_by = self._maintained(DataStructureDefinition,
                                            elem.attrib['structureRef'])

        # Process series
        for series_key, obs_list in values.pop('series', []):
            # Add observations under this key
            ds.add_obs(obs_list, series_key)

        # Process bare observations
        ds.add_obs(values.pop('obs', []))

        assert len(values) == 0
        return ds

    def parse_group(self, elem):
        """Both <generic:Group> and <structure:Group>."""
        values = self._parse(elem)

        # Check which namespace this Group tag is part of
        if elem.tag == qname('gen', 'Group'):
            # generic → GroupKey in a DataMessage
            gk = values.pop('groupkey')
            gk.attrib.update(values.pop('attributes', {}))
            result = gk
        elif elem.tag == qname('str', 'Group'):
            # structure → GroupDimensionDescriptor
            args = dict(components=values.pop('groupdimension'))
            gdd = GroupDimensionDescriptor(**args)
            result = gdd
        else:
            raise NotImplementedError(elem.tag)

        assert len(values) == 0
        return result

    def parse_key(self, elem):
        """SeriesKey, GroupKey, and observation dimensions."""
        cls = _parse_class['key'][self._stack[-1]]
        return cls({e.attrib['id']: e.attrib['value'] for e in
                    elem.iterchildren()})

    def parse_obs(self, elem):
        # TODO handle key-values as attribs
        values = self._parse(elem)
        key = (values['obskey'] if 'obskey' in values else
               values['obsdimension'])
        if 'obsdimension' in values:
            new_key = Key()
            new_key[key.id] = key
            key = new_key
        result = Observation(dimension=key, value=values['obsvalue'],
                             attached_attribute=values.get('attributes', {}))
        return result

    def parse_obsdimension(self, elem):
        args = dict(value=elem.attrib.pop('value'))
        args['id'] = elem.attrib.pop('id', self._obs_dim[0].id)
        assert len(elem.attrib) == 0
        return KeyValue(**args)

    def parse_obsvalue(self, elem):
        return elem.attrib['value']

    def parse_series(self, elem):
        values = self._parse(elem)
        series_key = values.pop('serieskey')
        series_key.attrib.update(values.pop('attributes', {}))
        obs_list = wrap(values.pop('obs', []))
        for o in obs_list:
            o.series_key = series_key
        assert len(values) == 0
        return (series_key, obs_list)

    # Parsers for elements appearing in structure messages

    def parse_structures(self, elem):
        return self._parse(elem, unwrap=False)

    def parse_organisation(self, elem):
        cls = _parse_class['organisation'][self._stack[-1]]
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
        c, values = self._named(Category, elem)
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

    def parse_orgscheme(self, elem):
        cls = _parse_class['orgscheme'][self._stack[-1]]
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
        Grouping = _parse_class['grouping'][elem.attrib.pop('id')]
        g = Grouping(**elem.attrib)
        g.components.extend(self._parse(elem, list, unwrap=False))
        return g

    def parse_dimension(self, elem):
        values = self._parse(elem)

        attrs = {}
        try:
            attrs['order'] = int(elem.attrib.pop('position'))
        except KeyError:
            pass

        d = Dimension(
            concept_identity=values.pop('conceptidentity'),
            local_representation=values.pop('localrepresentation'),
            **ChainMap(attrs, elem.attrib),
            )
        assert len(values) == 0
        return d

    # TODO should return a TimeDimension
    parse_timedimension = parse_dimension

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
        if tags == {qname('str', 'Dimension')}:
            values = self._parse(elem)
            ar = DimensionRelationship(dimensions=values.pop('dimension'))
            assert len(values) == 0
        elif tags == {qname('str', 'PrimaryMeasure')}:
            # Avoid recurive _parse() here, because it may contain a Ref to
            # a PrimaryMeasure that is not yet defined
            ar = PrimaryMeasureRelationship()
        elif tags == {qname('str', 'None')}:
            ar = NoSpecifiedRelationship()
        else:
            raise NotImplementedError('cannot parse %s' % etree.tostring(elem))
        return ar

    def parse_representation(self, elem):
        r = Representation()
        values = self._parse(elem, unwrap=False)
        if 'enumeration' in values:
            for e in values.pop('enumeration'):
                if isinstance(e, str):
                    e = ItemScheme(urn=e)
                r.enumerated = e
        elif 'textformat' in values:
            r.non_enumerated = set(values.pop('textformat'))
        assert len(values) == 0
        return r

    def parse_textformat(self, elem):
        """<str:TextFormat> tag defines an SDMX-IM Facet."""
        # Convert case of the value_type. In XML, first letter is uppercase;
        # in the spec, lowercase.
        value_type = elem.attrib.pop('textType', None)
        if isinstance(value_type, str):
            value_type = value_type[0].lower() + value_type[1:]
        f = Facet(value_type=value_type)
        key_map = {
            'minValue': 'min_value',
            'maxValue': 'max_value',
            'maxLength': 'max_length',
            }
        for key, value in elem.attrib.items():
            setattr(f.type, key_map.get(key, key), value)
        return f

    # Parsers for elements appearing in error messages

    def parse_errormessage(self, elem):
        values = self._parse(elem)
        values['text'] = [InternationalString(values['text'])]
        values['code'] = elem.attrib['code']
        return values
