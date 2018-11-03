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

from lxml import etree
from lxml.etree import QName, XPath

from pandasdmx.model import (
    DEFAULT_LOCALE,
    Agency,
    Annotation,
    AttributeDescriptor,
    # AttributeRelationship,
    # NoSpecifiedRelationship,
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
    DataAttribute,
    DataflowDefinition,
    DataMessage,
    DataSet,
    DataStructureDefinition,
    Dimension,
    DimensionDescriptor,
    Facet,
    Footer,
    GroupKey,
    Header,
    IdentifiableArtefact,
    InternationalString,
    ItemScheme,
    MeasureDescriptor,
    Key,
    KeyValue,
    Observation,
    PrimaryMeasure,
    Representation,
    SeriesKey,
    StructureMessage,
    TimeKeyValue,
    UsageStatus,
    )

from pandasdmx.reader import BaseReader

_ns = {
    'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
    'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
    'mes': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
    'gen': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
    'footer':
        'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message/footer',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    }

QNAME = {name: QName(_ns[ns], name) for ns, name in (
    ('com', 'Name'),
    ('xml', 'lang'),
    ('str', 'Dimension'),
    ('str', 'PrimaryMeasure'),
    )}

# Add namespaces
_message_class = {QName(_ns['mes'], name): cls for name, cls in (
    ('Structure', StructureMessage),
    ('GenericData', DataMessage),
    ('GenericTimeSeriesData', DataMessage),
    )}

_collect_paths = {
    'header': {
        'id': 'mes:ID/text()',
        'prepared': 'mes:Prepared/text()',
        'sender': 'mes:Sender/@*',
        'receiver': 'mes:Receiver/@*',
        },
    'obs': {
        'dimension': 'gen:ObsDimension/@value',
        'value': 'gen:ObsValue/@value',
        'attribs': 'gen:Attributes',
        },
    }

for group, vals in _collect_paths.items():
    for key, path in vals.items():
        _collect_paths[group][key] = XPath(path, namespaces=_ns,
                                           smart_strings=False)


_parse_alias = {
    'annotationtext': 'international_string',
    'name': 'international_string',
    'description': 'international_string',
    'text': 'international_string',
    'dimensionlist': 'grouping',
    'attributelist': 'grouping',
    'measurelist': 'grouping',
    'corerepresentation': 'representation',
    'localrepresentation': 'representation',
    'urn': 'string',
    }

# Class names stored as strings in XML attributes -> pandasdmx.model classes
_parse_class = {
    'grouping': {
        'DimensionDescriptor': DimensionDescriptor,
        'AttributeDescriptor': AttributeDescriptor,
        'MeasureDescriptor': MeasureDescriptor,
        },
    'ref': {
        'Codelist': Codelist,
        'Concept': Concept,
        'Category': Category,
        'Dataflow': DataflowDefinition,
        'DataStructure': DataStructureDefinition,
        },
    }


_parse_skip_level = [
    # Bare XML containers for other elements
    'annotations',
    'categoryschemes',
    'categorisations',
    'codelists',
    'concepts',
    'dataflows',
    'datastructures',
    'datastructurecomponents',
    'footer',
    # Contain only references
    'source',
    'structure',  # str:Structure, not mes:Structure
    'target',
    'conceptidentity',
    'enumeration',
    ]


def add_group_attributes(observations, groups):
    for obs in observations:
        for group_key, group_attrs in groups:
            if group_key in obs.key:
                obs.attrib.update(group_attrs)
        yield obs


def add_localizations(target, values):
    if isinstance(values, tuple) and len(values) == 2:
        values = [values]
    target.localizations.update({locale: label for locale, label in values})


def wrap(value):
    return value if isinstance(value, list) else [value]


class Reader(BaseReader):
    """
    Read SDMX-ML 2.1 and expose it as instances from pandasdmx.model
    """

    def initialize(self, source):
        # State variables for reader
        self._stack = []
        self._index = {}
        self._context = {}

        root = etree.parse(source).getroot()

        # Message class
        cls = _message_class[root.tag]

        # MAYBE use a factory method in DataMessage instead
        self._context['obs_dim_cls'] = (TimeKeyValue if 'TimeSeries' in
                                        root.tag else KeyValue)

        # Parse the tree
        try:
            values = self._parse(root)
        except Exception:
            print(' > '.join(self._stack))
            raise

        # Base message object
        msg = cls(header=values.pop('header'),
                  footer=values.pop('footer', None))

        # Finalize according to the message type
        if cls is DataMessage:
            dataset = values.pop('dataset')
            dataset = [dataset] if not isinstance(dataset, list) else dataset
            msg.data.extend(dataset)
        elif cls is StructureMessage:
            structures = values.pop('structures')

            # Dictionaries by ID
            for name in ('dataflow', 'codelist'):
                for obj in structures.pop(name + 's', []):
                    getattr(msg, name)[obj.id] = obj

            # Single objects
            for attr, name in (
                    ('structure', 'datastructures'),
                    ('category_scheme', 'categoryschemes'),
                    ('concept_scheme', 'concepts'),
                    ):
                obj_list = structures.pop(name, [None])
                assert len(obj_list) == 1
                setattr(msg, attr, obj_list[0])

            # Commented: the following don't work for e.g. insee-dataflow.xml,
            # which contains many Dataflows and no Structure
            # # Add associations
            # msg.dataflow.structure = msg.structure

            # The specimen XML messages only include a single Categorisation,
            # linking the DataflowDefinition to the CategoryScheme
            for c in structures.pop('categorisations', []):
                assert (c.category in msg.category_scheme and
                        c.artefact in msg.dataflows.values())

            assert len(structures) == 0

        assert len(values) == 0, values
        return msg

    def _collect(self, group, elem):
        result = {}
        for key, xpath in _collect_paths[group].items():
            matches = xpath(elem)
            if len(matches) > 1:
                result[key] = matches
            elif len(matches):
                result[key] = matches[0]
        return result

    def _parse(self, elem, rtype=dict, unwrap=True):
        """Recursively parse the XML *elem* and return pandasdmx.model objects.

        Methods like 'Reader.parse_attribute()' are called for XML elements
        with tag names like '<namespace:Attribute>'. Return type depends on
        *rtype*:
        - dict: a mapping of tag names to lists of objects.
        - list: a list of objects.

        If *unwrap* is True (the default), then single-entry lists are returned
        as bare objects.
        """
        # Container for results
        results = rtype()

        # Parse each child
        for child in elem:
            # Tag name for the child
            tag_name = child.tag.split('}')[-1].lower()

            # Store state
            self._stack.append(tag_name)

            # Invoke the parser for this element
            if tag_name in _parse_skip_level:
                # Element doesn't require any special parsing; immediately
                # parse its children as a list
                self._stack[-1] += ' (skip)'
                result = self._parse(child, rtype=list, unwrap=False)
            elif len(child) == 1 and child[0].tag == 'Ref':
                # Parse or look up a reference
                result = [self.parse_ref(child[0])]
            else:
                # Parse the element, maybe using an alias
                method = 'parse_' + _parse_alias.get(tag_name, tag_name)
                result = [getattr(self, method)(child)]

            # Index object names
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
                results = {k: v[0] if len(v) == 1 else v for k, v in
                           results.items()}
            else:
                results = results[0] if len(results) == 1 else results

        return results

    def _named(self, cls, elem, **kwargs):
        """Shortcut for parsing NameableArtefacts."""
        # Instantiate the *cls* and store the attributes
        _named_attrs_convert = {
            'agencyID': ('maintainer', lambda value: Agency(id=value)),
            'isFinal': ('is_final', bool),
            'isPartial': ('is_partial', bool),
            }

        attrs = {}
        for source, (target, xform) in _named_attrs_convert.items():
            try:
                value = elem.attrib.pop(source)
            except KeyError:
                continue
            else:
                attrs[target] = xform(value) if callable(xform) else value

        obj = cls(**ChainMap(attrs, elem.attrib))

        # Parse  children, including localizations for the name
        values = self._parse(elem, **kwargs)

        # Store the name, description, and annotations
        add_localizations(obj.name, values.pop('name'))
        add_localizations(obj.description, values.pop('description', []))
        obj.annotations = wrap(values.pop('annotations', []))

        # Return the instance and any non-name values
        return obj, values

    def parse_string(self, elem):
        return elem.text

    # Data messages

    def parse_attributes(self, elem):
        result = {}
        for e in elem.iterchildren():
            da = DataAttribute(id=e.attrib['id'])
            av = AttributeValue(value_for=da, value=e.attrib['value'])
            result[da] = av
        return result

    def parse_header(self, elem):
        return Header(**self._collect('header', elem))

    def parse_message(self, elem):
        f = Footer(**elem.attrib)
        for locale, label in self._parse(elem)['text']:
            f.text.append(InternationalString(**{locale: label}))
        return f

    def parse_dataset(self, elem):
        ds = DataSet()
        values = self._parse(elem)
        groups = values.get('groups', [])
        # Add parsed observations to the dataset
        for obs_list in values.get('series', []):
            ds.obs.extend(add_group_attributes(obs_list, groups))
        ds.obs.extend(add_group_attributes(values.get('obs', []), groups))
        return ds

    def parse_group(self, elem):
        values = self._parse(elem)
        return (values['groupkey'], values['attributes'])

    def parse_groupkey(self, elem):
        return GroupKey({e.attrib['id']: e.attrib['value'] for e in
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
                             attrib=values.get('attributes', {}))
        return result

    def parse_obsdimension(self, elem):
        return self._context['obs_dim_cls'](**elem.attrib)

    def parse_obskey(self, elem):
        result = Key()
        for e in elem.iterchildren():
            result[e.attrib['id']] = e.attrib['value']
        return result

    def parse_obsvalue(self, elem):
        return elem.attrib['value']

    def parse_series(self, elem):
        results = self._parse(elem)
        for o in results['obs']:
            o.series_key = results['serieskey']
            o.attrib.update(results.get('attributes', {}))
        return results['obs']

    def parse_serieskey(self, elem):
        return SeriesKey({e.attrib['id']: e.attrib['value'] for e in
                          elem.iterchildren()})

    # Structure messages

    def parse_international_string(self, elem):
        locale = elem.attrib.get(QNAME['lang'], DEFAULT_LOCALE)
        return (locale, elem.text)

    def parse_annotation(self, elem):
        values = self._parse(elem)
        for target, source in [('type', 'annotationtype'),
                               ('text', 'annotationtext')]:
            try:
                values[target] = values.pop(source)
            except KeyError:
                continue
        return Annotation(**values)

    def parse_annotationtype(self, elem):
        return elem.text

    def parse_code(self, elem):
        c, values = self._named(Code, elem)
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
        cl.items.extend(values.pop('code'))
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

    def parse_conceptscheme(self, elem):
        cs, values = self._named(ConceptScheme, elem)
        cs.items = values.pop('concept')
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

    def parse_attribute(self, elem):
        attrs = {k: elem.attrib[k] for k in ('id', 'urn')}
        attrs['usage_status'] = UsageStatus[
                                       elem.attrib['assignmentStatus'].lower()]
        values = self._parse(elem)
        da = DataAttribute(
            concept_identity=values.pop('conceptidentity'),
            local_representation=values.pop('localrepresentation'),
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
        if tags == {QNAME['Dimension']}:
            values = self._parse(elem)
            ar = DimensionRelationship(dimensions=values.pop('dimension'))
            assert len(values) == 0
        elif tags == {QNAME['PrimaryMeasure']}:
            # Avoid recurive _parse() here, because it may contain a Ref to
            # a PrimaryMeasure that is not yet defined
            ar = PrimaryMeasureRelationship()
        else:
            raise NotImplementedError
        return ar

    def parse_representation(self, elem):
        r = Representation()
        values = self._parse(elem, unwrap=False)
        if 'enumeration' in values:
            for e in values.pop('enumeration'):
                if isinstance(e, str):
                    e = ItemScheme(urn=e)
                r.enumerated.append(e)
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

    def parse_ref(self, elem):
        """External and internal references MaintainableArtefacts."""
        try:
            # If the element has a 'class' attribute, this gives the class
            # directly
            cls = _parse_class['ref'][elem.attrib['class']]

            # Instantiate the external reference
            ref = cls(
                id=elem.attrib['id'],
                # is_external_reference=True,
                # maintainer=Agency(id=elem.attrib['agencyID'])
                )

            # Store the version
            try:
                ref.version = elem.attrib['version']
            except KeyError:
                pass
        except KeyError:
            # Internal reference
            # TODO sometimes this is -1; sometimes -2
            for depth in -1, -2:
                try:
                    class_name = self._stack[depth].capitalize()
                    ref = self._index[(class_name, elem.attrib['id'])]
                    break
                except KeyError:
                    continue
        return ref

    def parse_structures(self, elem):
        return self._parse(elem, unwrap=False)
