# encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a reader for SDMXML v2.1.

'''

from pandasdmx.utils import DictLike, namedtuple_factory
from pandasdmx import model
from pandasdmx.reader import BaseReader
from lxml import etree
from lxml.etree import XPath


class Reader(BaseReader):

    """
    Read SDMX-ML 2.1 and expose it as instances from pandasdmx.model
    """

    _nsmap = {
        'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
        'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
        'mes': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
        'gen': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
        'footer': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message/footer'
    }

    def initialize(self, source):
        # Compile the above xpath expressions if not already done
        if type(self._paths['urn']) is str:
            self._compile_paths()
        tree = etree.parse(source)
        root = tree.getroot()
        if root.tag.endswith('Structure'):
            cls = model.StructureMessage
        elif (root.tag.endswith('GenericData')
              or root.tag.endswith('GenericTimeSeriesData')):
            cls = model.GenericDataMessage
        elif (root.tag.endswith('StructureSpecificData')
              or root.tag.endswith('StructureSpecificTimeSeriesData')):
            cls = model.StructureSpecificDataMessage
        else:
            raise ValueError('Unsupported root tag: %s' % root.tag)
        self.message = cls(self, root)
        return self.message

    _root_tag = XPath('name(//*[1])')

    _paths = {
        'footer_text': 'com:Text/text()',
        'footer_code': '@code',
        'footer_severity': '@severity',
        'dataflow_from_msg': 'mes:Structures/str:Dataflows',
        'constraint_attachment': 'str:ConstraintAttachment',
        'include': '@include',
        'id': '@id',
        'urn': '@urn',
        'url': '@url',
        'uri': '@uri',
        'agencyID': '@agencyID',
        'value': 'com:Value/text()',
        'headerID': 'mes:ID/text()',
        'header_prepared': 'mes:Prepared/text()',
        'header_sender': 'mes:Sender/@*',
        'ref_version': '@version',
        'position': '@position',
        'isfinal': '@isfinal',
        'ref_package': '@package',
        'ref_class': '@class',
        'ref_target': 'str:Target',
        'ref_source': 'str:Source',
        'ref_structure': 'str:Structure',
        'annotationtype': 'com:AnnotationType/text()',
        'structured_by': 'mes:Structure/@structureID',
        'dim_at_obs': '//mes:Header/mes:Structure/@dimensionAtObservation',
        'generic_obs_path': 'gen:Obs',
        'obs_key_id_path': 'gen:ObsKey/gen:Value/@id',
        'obs_key_values_path': 'gen:ObsKey/gen:Value/@value',
        'series_key_values_path': 'gen:SeriesKey/gen:Value/@value',
        'series_key_id_path':        'gen:SeriesKey/gen:Value/@id',
        'generic_series_dim_path': 'gen:ObsDimension/@value',
        'group_key_values_path': 'gen:GroupKey/gen:Value/@value',
        'group_key_id_path': 'gen:GroupKey/gen:Value/@id',
        'obs_value_path': 'gen:ObsValue/@value',
        'attr_id_path': 'gen:Attributes/gen:Value/@id',
        'attr_values_path': 'gen:Attributes/gen:Value/@value',
        model.Code: 'str:Code',
        model.Categorisation: 'str:Categorisation',
        model.CategoryScheme: 'mes:Structures/str:CategorySchemes/str:CategoryScheme',
        model.DataStructureDefinition: 'mes:Structures/str:DataStructures/str:DataStructure',
        model.DataflowDefinition: 'str:Dataflow',
        model.ConceptScheme: 'mes:Structures/str:Concepts/str:ConceptScheme',
        model.ContentConstraint: 'mes:Structures/str:Constraints/str:ContentConstraint',
        model.Concept: 'str:Concept',
        model.Codelist: 'mes:Structures/str:Codelists/str:Codelist',
        model.Categorisations: 'mes:Structures/str:Categorisations',
        model.Footer: 'footer:Footer/footer:Message',
        model.Category: 'str:Category',
        model.DimensionDescriptor: 'str:DataStructureComponents/str:DimensionList',
        model.Dimension: 'str:Dimension',
        model.TimeDimension: 'str:TimeDimension',
        model.MeasureDimension: 'str:MeasureDimension',
        model.MeasureDescriptor: 'str:DataStructureComponents/str:MeasureList',
        model.PrimaryMeasure: 'str:PrimaryMeasure',
        model.AttributeDescriptor: 'str:DataStructureComponents/str:AttributeList',
        model.DataAttribute: 'str:Attribute',
        model.CubeRegion: 'str:CubeRegion',
        model.KeyValue: 'com:KeyValue',
        model.Ref: 'Ref',
        model.Header: 'mes:Header',
        model.Annotation: 'com:Annotations/com:Annotation',
        model.Group: 'gen:Group',
        model.Series: 'gen:Series',
        model.GenericDataSet: 'mes:DataSet',
    }

    def _compile_paths(self):
        for key, path in self._paths.items():
            self._paths[key] = XPath(path, namespaces=self._nsmap)

    def read_identifiables(self, cls,  sdmxobj, offset=None):
        '''
        If sdmxobj inherits from dict: update it  with modelized elements.
        These must be instances of model.IdentifiableArtefact,
        i.e. have an 'id' attribute. This will be used as dict keys.
        If sdmxobj does not inherit from dict: return a new DictLike.
        '''
        path = self._paths[cls]
        if offset:
            try:
                base = self._paths[offset](sdmxobj._elem)[0]
            except IndexError:
                return None
        else:
            base = sdmxobj._elem
        result = {e.get('id'): cls(self, e) for e in path(base)}
        if isinstance(sdmxobj, dict):
            sdmxobj.update(result)
        else:
            return DictLike(result)

    def read_instance(self, cls, sdmxobj, offset=None, first_only=True):
        '''
        If cls in _paths and matches,
        return an instance of cls with the first XML element,
        or, if fest_only is False, a list of cls instances 
        for all elements found,
        If no matches were found, return None.  
        '''
        if offset:
            try:
                base = self._paths[offset](sdmxobj._elem)[0]
            except IndexError:
                return None
        else:
            base = sdmxobj._elem
        result = self._paths[cls](base)
        if result:
            if first_only:
                return cls(self, result[0])
            else:
                return [cls(self, i) for i in result]

    def read_as_str(self, name, sdmxobj, first_only=True):
        result = self._paths[name](sdmxobj._elem)
        if result:
            if first_only:
                return result[0]
            else:
                return result

    def international_str(self, name, sdmxobj):
        '''
        return DictLike of xml:lang attributes. If node has no attributes,
        assume that language is 'en'.
        '''
        # Get language tokens like 'en', 'fr'...
        # Can we simplify the xpath expressions by not using .format?
        elem_attrib = sdmxobj._elem.xpath('com:{0}/@xml:lang'.format(name),
                                          namespaces=self._nsmap)
        values = sdmxobj._elem.xpath('com:{0}/text()'.format(name),
                                     namespaces=self._nsmap)
        # Unilingual strings have no attributes. Assume 'en' instead.
        if not elem_attrib:
            elem_attrib = ['en']
        return DictLike(zip(elem_attrib, values))

    def header_sender(self, sdmxobj):
        return DictLike(sdmxobj._elem.Sender.attrib)

    def header_error(self, sdmxobj):
        try:
            return DictLike(sdmxobj._elem.Error.attrib)
        except AttributeError:
            return None

    def isfinal(self, sdmxobj):
        return bool(sdmxobj._elem.get('isFinal'))

    def concept_id(self, sdmxobj):
        # called by model.Component.concept
        c_id = sdmxobj._elem.xpath('str:ConceptIdentity/Ref/@id',
                                   namespaces=self._nsmap)[0]
        parent_id = sdmxobj._elem.xpath('str:ConceptIdentity/Ref/@maintainableParentID',
                                        namespaces=self._nsmap)[0]
        return self.message.conceptschemes[parent_id][c_id]

    def localrepr(self, sdmxobj):
        node = sdmxobj._elem.xpath('str:LocalRepresentation',
                                   namespaces=self._nsmap)[0]
        enum = node.xpath('str:Enumeration/Ref/@id',
                          namespaces=self._nsmap)
        if enum:
            enum = self.message.codelists[enum[0]]
        else:
            enum = None
        return model.Representation(self, node, enum=enum)

    def assignment_status(self, sdmxobj):
        return sdmxobj._elem.get('assignmentStatus')

    def attr_relationship(self, sdmxobj):
        return sdmxobj._elem.xpath('*/Ref/@id')

    # Types and xpath expressions for generic observations
    _ObsTuple = namedtuple_factory(
        'GenericObservation', ('key', 'value', 'attrib'))
    _SeriesObsTuple = namedtuple_factory(
        'SeriesObservation', ('dim', 'value', 'attrib'))

    def iter_generic_obs(self, sdmxobj, with_value, with_attributes):
        for obs in self._paths['generic_obs_path'](sdmxobj._elem):
            # Construct the namedtuple for the ObsKey.
            # The namedtuple class is created on first iteration.
            obs_key_values = self._paths['obs_key_values_path'](obs)
            try:
                obs_key = ObsKeyTuple._make(obs_key_values)
            except NameError:
                obs_key_id = self._paths['obs_key_id_path'](obs)
                ObsKeyTuple = namedtuple_factory('ObsKey', obs_key_id)
                obs_key = ObsKeyTuple._make(obs_key_values)
            if with_value:
                obs_value = self._paths['obs_value_path'](obs)[0]
            else:
                obs_value = None
            if with_attributes:
                obs_attr_values = self._paths['attr_values_path'](obs)
                obs_attr_id = self._paths['attr_id_path'](obs)
                obs_attr_type = namedtuple_factory(
                    'ObsAttributes', obs_attr_id)
                obs_attr = obs_attr_type(*obs_attr_values)
            else:
                obs_attr = None
            yield self._ObsTuple(obs_key, obs_value, obs_attr)

    def generic_series(self, sdmxobj):
        path = self._paths[model.Series]
        for series in path(sdmxobj._elem):
            yield model.Series(self, series, dataset=sdmxobj)

    def generic_groups(self, sdmxobj):
        path = self._paths[model.Group]
        for series in path(sdmxobj._elem):
            yield model.Group(self, series)

    def series_key(self, sdmxobj):
        series_key_id = self._paths['series_key_id_path'](sdmxobj._elem)
        series_key_values = self._paths[
            'series_key_values_path'](sdmxobj._elem)
        SeriesKeyTuple = namedtuple_factory('SeriesKey', series_key_id)
        return SeriesKeyTuple._make(series_key_values)

    def group_key(self, sdmxobj):
        group_key_id = self._paths['group_key_id_path'](sdmxobj._elem)
        group_key_values = self._paths[
            'group_key_values_path'](sdmxobj._elem)
        GroupKeyTuple = namedtuple_factory('GroupKey', group_key_id)
        return GroupKeyTuple._make(group_key_values)

    def series_attrib(self, sdmxobj):
        attr_id = self._paths['attr_id_path'](sdmxobj._elem)
        attr_values = self._paths['attr_values_path'](sdmxobj._elem)
        return namedtuple_factory('Attrib', attr_id)(*attr_values)

    def iter_generic_series_obs(self, sdmxobj, with_value, with_attributes,
                                reverse_obs=False):
        for obs in sdmxobj._elem.iterchildren(
                '{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Obs',
                reversed=reverse_obs):
            obs_dim = self._paths['generic_series_dim_path'](obs)[0]
            if with_value:
                obs_value = self._paths['obs_value_path'](obs)[0]
            else:
                obs_value = None
            if with_attributes:
                obs_attr_values = self._paths['attr_values_path'](obs)
                obs_attr_id = self._paths['attr_id_path'](obs)
                obs_attr_type = namedtuple_factory(
                    'ObsAttributes', obs_attr_id)
                obs_attr = obs_attr_type(*obs_attr_values)
            else:
                obs_attr = None
            yield self._SeriesObsTuple(obs_dim, obs_value, obs_attr)
