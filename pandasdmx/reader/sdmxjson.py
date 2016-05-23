#! encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014-2016 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a reader for SDMXML v2.1.

'''

from pandasdmx.utils import DictLike, namedtuple_factory
from pandasdmx import model
from pandasdmx.reader import BaseReader
import json
from jsonpath_rw import parse
from operator import itemgetter


class XPath:

    def __init__(self, path):
        self.path = parse(path)

    def __call__(self, elem):
        return self.path.find(elem)


class Reader(BaseReader):

    """
    Read SDMXJSON 2.1 and expose it as instances from pandasdmx.model
    """

    def read_as_str(self, name, sdmxobj, first_only=True):
        result = self._paths[name](sdmxobj._elem)
        if result:
            if first_only:
                return result[0].value
            else:
                return [r.value for r in result]

    def initialize(self, source):
        tree = json.load(source)
        cls = model.DataMessage
        self.message = cls(self, tree)
        return self.message

    # flag to prevent multiple compiling. See BaseReader.__init__
    _compiled = False

    def write_source(self, filename):
        '''
        Save source to file by calling `write` on the root element.
        '''
        return json.dumps(self.message._elem, filename)

    _paths = {
        #         'footer_text': 'com:Text/text()',
        #         'footer_code': '@code',
        #         'footer_severity': '@severity',
        #         'dataflow_from_msg': 'mes:Structures/str:Dataflows',
        #         'constraint_attachment': 'str:ConstraintAttachment',
        #         'include': '@include',
        #         'id': '@id',
        #         'urn': '@urn',
        #         'url': '@url',
        #         'uri': '@uri',
        #         'agencyID': '@agencyID',
        #         'maintainable_parent_id': '@maintainableParentID',
        #         'value': 'com:Value/text()',
        'headerID': 'id',
        #         'header_prepared': 'mes:Prepared/text()',
        #         'header_sender': 'mes:Sender/@*',
        #         'header_receiver': 'mes:Receiver/@*',
        #         'assignment_status': '@assignmentStatus',
        #         'error': 'mes:error/@*',
        #         'ref_version': '@version',
        #         'concept_id': 'str:ConceptIdentity',
        #         'position': '@position',
        #         'isfinal': '@isfinal',
        #         'ref_package': '@package',
        #         'ref_class': '@class',
        #         'ref_target': 'str:Target',
        #         'ref_source': 'str:Source',
        #         'ref_structure': 'str:Structure',
        #         'annotationtype': 'com:AnnotationType/text()',
        'structured_by': '$.structure.links',
        'dim_at_obs': '$.structure.dimensions.observations',
        #         'generic_obs_path': 'gen:Obs',
        #         'obs_key_id_path': 'gen:ObsKey/gen:Value/@id',
        #         'obs_key_values_path': 'gen:ObsKey/gen:Value/@value',
        #         'series_key_values_path': 'gen:SeriesKey/gen:Value/@value',
        #         'series_key_id_path':        'gen:SeriesKey/gen:Value/@id',
        #         'generic_series_dim_path': 'gen:ObsDimension/@value',
        #         'group_key_values_path': 'gen:GroupKey/gen:Value/@value',
        #         'group_key_id_path': 'gen:GroupKey/gen:Value/@id',
        #         'obs_value_path': 'gen:ObsValue/@value',
        #         'attr_id_path': 'gen:Attributes/gen:Value/@id',
        #         'attr_values_path': 'gen:Attributes/gen:Value/@value',
        #         model.Code: 'str:Code',
        #         model.Categorisation: 'str:Categorisation',
        #         model.CategoryScheme: 'mes:Structures/str:CategorySchemes/str:CategoryScheme',
        #         model.DataStructureDefinition: 'mes:Structures/str:DataStructures/str:DataStructure',
        #         model.DataflowDefinition: 'str:Dataflow',
        #         model.ConceptScheme: 'mes:Structures/str:Concepts/str:ConceptScheme',
        #         model.ContentConstraint: 'mes:Structures/str:Constraints/str:ContentConstraint',
        #         model.Concept: 'str:Concept',
        #         model.Codelist: 'mes:Structures/str:Codelists/str:Codelist',
        #         model.Categorisations: 'mes:Structures/str:Categorisations',
        model.Footer: 'footer.message',
        #         model.Category: 'str:Category',
        #         model.DimensionDescriptor: 'str:DataStructureComponents/str:DimensionList',
        #         model.Dimension: 'str:Dimension',
        #         model.TimeDimension: 'str:TimeDimension',
        #         model.MeasureDimension: 'str:MeasureDimension',
        #         model.MeasureDescriptor: 'str:DataStructureComponents/str:MeasureList',
        #         model.PrimaryMeasure: 'str:PrimaryMeasure',
        #         model.AttributeDescriptor: 'str:DataStructureComponents/str:AttributeList',
        #         model.DataAttribute: 'str:Attribute',
        #         model.CubeRegion: 'str:CubeRegion',
        #         model.KeyValue: 'com:KeyValue',
        #         model.Ref: 'Ref',
        model.Header: 'header',
        #         model.Annotation: 'com:Annotations/com:Annotation',
        #         model.Group: 'gen:Group',
        #         model.Series: 'gen:Series',
        model.DataSet: 'dataSets[0]',
        #         'int_str_names': './*[local-name() = $name]/@xml:lang',
        #         model.Representation: 'str:LocalRepresentation',
        #         'int_str_values': './*[local-name() = $name]/text()',
        #         'enumeration': 'str:Enumeration',
        #         'texttype': 'str:TextFormat/@textType',
        #         'maxlength': 'str:TextFormat/@maxLength',
        #         # need this? It is just a non-offset Ref
        #         'attr_relationship': '*/Ref/@id',
    }

    @classmethod
    def _compile_paths(cls):
        for key, path in cls._paths.items():
            cls._paths[key] = XPath(path)

    def international_str(self, name, sdmxobj):
        '''
        return DictLike of xml:lang attributes. If node has no attributes,
        assume that language is 'en'.
        '''
        # Get language tokens like 'en', 'fr'...
        elem_attrib = self._paths['int_str_names'](sdmxobj._elem, name=name)
        values = self._paths['int_str_values'](sdmxobj._elem, name=name)
        # Unilingual strings have no attributes. Assume 'en' instead.
        if not elem_attrib:
            elem_attrib = ['en']
        return DictLike(zip(elem_attrib, values))

    def header_error(self, sdmxobj):
        try:
            return DictLike(sdmxobj._elem.Error.attrib)
        except AttributeError:
            return None

    # Types for generic observations
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

    @staticmethod
    def getitem_key(obj):
        return obj.value['_key']

    def generic_series(self, sdmxobj):
        for key, series in sdmxobj._elem.value['series'].items():
            series['_key'] = key
        for series in sorted(parse('series.*').find(sdmxobj._elem), key=self.getitem_key):
            yield model.Series(self, series, dataset=sdmxobj)

    def generic_groups(self, sdmxobj):
        return []

    def series_key(self, sdmxobj):
        # pull down dataset key
        dataset_dim = parse(
            '$.structure.dimensions.dataSet[*]').find(sdmxobj._elem)
        full_key_ids = [d.value['id'] for d in dataset_dim]
        full_key_values = [d.value['values'][0]['id'] for d in dataset_dim]
        key_idx = [int(i) for i in sdmxobj._elem.value['_key'].split(':')]
        struct_dim = parse('$.structure.dimensions.series').find(
            sdmxobj._elem)[0].value
        series_key_ids = [d['id'] for d in struct_dim]
        series_key_values = [d['values'][i]['id'] for i, d in
                             zip(key_idx, struct_dim)]
        full_key_ids.extend(series_key_ids)
        full_key_values.extend(series_key_values)
        SeriesKeyTuple = namedtuple_factory('SeriesKey', full_key_ids)
        return SeriesKeyTuple._make(full_key_values)

    def group_key(self, sdmxobj):
        group_key_id = self._paths['group_key_id_path'](sdmxobj._elem)
        group_key_values = self._paths[
            'group_key_values_path'](sdmxobj._elem)
        GroupKeyTuple = namedtuple_factory('GroupKey', group_key_id)
        return GroupKeyTuple._make(group_key_values)

    def dataset_attrib(self, sdmxobj):
        value_idx = sdmxobj._elem.value.get('attributes')
        if value_idx:
            struct_attrib = parse('$.structure.attributes.dataset').find(
                sdmxobj._elem)[0].value
            return [(a['id'],
                     a['values'][i].get('id', a['values'][i]['name']))
                    for i, a in zip(value_idx, struct_attrib)]

    def series_attrib(self, sdmxobj):
        value_idx = sdmxobj._elem.value.get('attributes')
        if value_idx:
            struct_attrib = parse('$.structure.attributes.series').find(
                sdmxobj._elem)[0].value
            return [(a['id'],
                     a['values'][i].get('id', a['values'][i]['name']))
                    for i, a in zip(value_idx, struct_attrib)]
    getitem0 = itemgetter(0)

    def iter_generic_series_obs(self, sdmxobj, with_value, with_attributes,
                                reverse_obs=False):
        obs_l = sorted(sdmxobj._elem.value[
                       'observations'].items(), key=self.getitem0, reverse=reverse_obs)
        obs_dim_l = parse(
            '$.structure.dimensions.observation[*]').find(sdmxobj._elem)
        for obs in obs_l:
            obs_dim = obs_dim_l[0].value['values'][int(obs[0])]['id']
            if with_value:
                obs_value = obs[1][0]
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
