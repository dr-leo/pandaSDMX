# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014-2016 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a reader for SDMXML v2.1.

'''
from lxml import etree
from lxml.etree import XPath

from pandasdmx.model import (
    DEFAULT_LOCALE,
    Annotation,
    AttributeValue,
    Code,
    Codelist,
    Concept,
    ConceptScheme,
    DataAttribute,
    DataMessage,
    DataSet,
    Footer,
    Header,
    InternationalString,
    GroupKey,
    Key,
    KeyValue,
    Observation,
    SeriesKey,
    StructureMessage,
    TimeKeyValue,
    )

from pandasdmx.reader import BaseReader

_nsmap = {
    'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
    'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
    'mes': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
    'gen': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
    'footer':
        'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message/footer',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    }

QNAME = {
    'Name': etree.QName(_nsmap['com'], 'Name').text,
    'lang': etree.QName(_nsmap['xml'], 'lang').text,
    }


message_tags = {
    StructureMessage: ['Structure'],
    DataMessage: ['GenericData', 'GenericTimeSeriesData'],
    }
# Add namespaces
for type, tags in message_tags.items():
    message_tags[type] = ['{{{}}}{}'.format(_nsmap['mes'], t) for t in tags]


class Reader(BaseReader):
    """
    Read SDMX-ML 2.1 and expose it as instances from pandasdmx.model
    """

    def initialize(self, source):
        root = etree.parse(source).getroot()
        self.msg = get_message_class(root.tag)()
        context = {
            'obs_dim_cls': (TimeKeyValue if 'TimeSeries' in root.tag else
                            KeyValue),
            }
        values = self._dispatch(root, context)
        self.msg.data.append(values.pop('dataset', None))
        # Store the footer, if any
        footer = values.pop('footer', None)
        if footer:
            self.msg.footer = footer[0]
        return self.msg

    def parse_attributes(self, elem, context):
        result = {}
        for e in elem.iterchildren():
            da = DataAttribute(id=e.attrib['id'])
            av = AttributeValue(value_for=da, value=e.attrib['value'])
            result[da] = av
        return result

    def parse_header(self, elem, context):
        values = self._collect('header', elem)
        self.msg.header = Header(**values)

    def parse_message(self, elem, context):
        f = Footer(**elem.attrib)
        for locale, label in self._dispatch(elem, context)['text']:
            f.text.append(InternationalString(**{locale: label}))
        return f

    def parse_dataset(self, elem, context):
        ds = DataSet()
        values = self._dispatch(elem, context)
        groups = values.get('groups', [])
        # Add parsed observations to the dataset
        for obs_list in values.get('series', []):
            ds.obs.extend(add_group_attributes(obs_list, groups))
        ds.obs.extend(add_group_attributes(values.get('obs', []), groups))
        return ds

    def parse_group(self, elem, context):
        values = self._dispatch(elem, context)
        return (values['groupkey'], values['attributes'])

    def parse_groupkey(self, elem, context):
        return GroupKey({e.attrib['id']: e.attrib['value'] for e in
                         elem.iterchildren()})

    def parse_obs(self, elem, context):
        # TODO handle key-values as attribs
        values = self._dispatch(elem, context)
        key = (values['obskey'] if 'obskey' in values else
               values['obsdimension'])
        if 'obsdimension' in values:
            new_key = Key()
            new_key[key.id] = key
            key = new_key
        result = Observation(dimension=key, value=values['obsvalue'],
                             attrib=values.get('attributes', {}))
        return result

    def parse_obsdimension(self, elem, context):
        return context['obs_dim_cls'](**elem.attrib)

    def parse_obskey(self, elem, context):
        result = Key()
        for e in elem.iterchildren():
            result[e.attrib['id']] = e.attrib['value']
        return result

    def parse_obsvalue(self, elem, context):
        return elem.attrib['value']

    def parse_series(self, elem, context):
        results = self._dispatch(elem, context)
        for o in results['obs']:
            o.series_key = results['serieskey']
            o.attrib.update(results.get('attributes', {}))
        return results['obs']

    def parse_serieskey(self, elem, context):
        return SeriesKey({e.attrib['id']: e.attrib['value'] for e in
                          elem.iterchildren()})

    # Structure

    def parse_international_string(self, elem, context):
        locale = elem.attrib.get(QNAME['lang'], DEFAULT_LOCALE)
        return (locale, elem.text)

    parse_annotationtext = parse_international_string
    parse_name = parse_international_string
    parse_description = parse_international_string
    parse_text = parse_international_string

    def parse_annotation(self, elem, context):
        return Annotation(**self._dispatch(elem, context))

    def parse_annotationtype(self, elem, context):
        return elem.text

    def parse_code(self, elem, context):
        c = Code(**elem.attrib)
        add_localizations(c.name, self._dispatch(elem, context, list))
        return c

    def parse_codelist(self, elem, context):
        cl = Codelist(**elem.attrib)
        values = self._dispatch(elem, context)
        add_localizations(cl.name, [values['name']])
        if isinstance(values['code'], Code):
            values['code'] = [values['code']]
        cl.items.extend(values['code'])
        return cl

    def parse_concept(self, elem, context):
        c = Concept(**self._dispatch(elem, context))
        # TODO implement
        raise NotImplementedError

    def parse_conceptscheme(self, elem, context):
        cs = ConceptScheme(**elem.attrib)
        values = self._dispatch(elem, context)
        print(values)
        raise NotImplementedError

    def parse_structures(self, elem, context):
        values = self._dispatch(elem, context)
        print(values)
        # TODO implement
        raise NotImplementedError

    _paths_new = {
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

    def _collect(self, group, elem):
        result = {}
        for key, xpath in self._paths_new[group].items():
            matches = xpath(elem)
            if len(matches) > 1:
                result[key] = matches
            elif len(matches):
                result[key] = matches[0]
        return result

    _dispatch_skip_level = ['annotations', 'codelists', 'concepts', 'footer']

    def _dispatch(self, elem, context={}, rtype=dict):
        results = rtype()
        for child in elem:
            tag_name = child.tag.split('}')[-1].lower()

            # Invoke the parser for this tag
            if tag_name in self._dispatch_skip_level:
                result = self._dispatch(child, context, list)
            else:
                result = getattr(self, 'parse_' + tag_name)(child, context)

            # Store the result
            if result:
                if rtype is list:
                    results.append(result)
                else:
                    results[tag_name] = results.get(tag_name, []) + [result]
        if rtype is dict:
            results = {k: v[0] if len(v) == 1 else v for k, v in
                       results.items()}
        return results


for group, vals in Reader._paths_new.items():
    for key, path in vals.items():
        Reader._paths_new[group][key] = XPath(path, namespaces=_nsmap,
                                              smart_strings=False)


def get_message_class(tag):
    for type, tags in message_tags.items():
        if tag in tags:
            return type
    raise ValueError(tag)


def add_group_attributes(observations, groups):
    for obs in observations:
        for group_key, group_attrs in groups:
            if group_key in obs.key:
                obs.attrib.update(group_attrs)
        yield obs


def add_localizations(target, values):
    target.localizations.update({locale: label for locale, label in values})
