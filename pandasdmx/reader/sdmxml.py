# encoding: utf-8


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
        'data': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/structurespecific',
        'footer': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message/footer'
    }

    def initialize(self, source):
        tree = etree.parse(source)
        root = tree.getroot()
        if root.tag.endswith('Structure'):
            msg = model.StructureMessage(self, root)
        elif (root.tag.endswith('GenericTimeSeriesData')
              or root.tag.endswith('GenericData')):
            msg = model.DataMessage(self, root)
            # remove any DSD so as not to misguide parsing methods
            self.dsd = None
        elif (root.tag.endswith('StructureSpecificTimeSeriesData')
              or root.tag.endswith('StructureSpecificData')):
            msg = model.DataMessage(self, root)
            # Exclude the rare case that the msg header does not contain a structure ID.
            # A known case is ESTAT returning a message indicating
            # that a large dataset is bing made available as downloadable zi file.
            # The caller must handle this, e.g., by analyzing any provided
            # footer.
            if hasattr(msg.header, 'structured_by'):
                # download the DSD if not already
                # provided by the caller at instantiation.
                if not self.dsd:
                    dsd_id_raw = msg.header.structured_by
                    # Some agencies such as ECB put the DSD ID into the structured_by field,
                    # others prepend the agency ID and append the version. We try
                    # to muddle through this mess. But there may be unknown
                    # pitfalls.
                    cache_id = self.request.agency + dsd_id_raw
                    try:
                        dsd_id = dsd_id_raw
                        self.dsd = self.request.datastructure(dsd_id,
                                                              params={
                                                                  'references': None},
                                                              cache=cache_id).datastructure[dsd_id]
                    except Exception:
                        self.request.clear_cache(cache_id)
                        # strip off leading agency ID and trailing version
                        start = dsd_id_raw.find('_') + 1
                        dsd_id = dsd_id_raw[start:-4]
                        self.dsd = self.request.datastructure(dsd_id,
                                                              params={
                                                                  'references': None},
                                                              cache=cache_id).datastructure[dsd_id]

                # extract dimension and attribute IDs from the DSD for later
                # use
                self.dim_ids = [d.id for d in self.dsd.dimensions.aslist()]
                self.attrib_ids = sorted(self.dsd.attributes.keys())
        else:
            raise ValueError('Unsupported root tag: %s' % root.tag)
        self.message = msg
        return msg

    # flag to prevent multiple compiling. See BaseReader.__init__
    _compiled = False

    def write_source(self, filename):
        '''
        Save XML source to file by calling `write` on the root element.
        '''
        return self.message._elem.getroottree().write(filename, encoding='utf8')

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
        'maintainable_parent_id': '@maintainableParentID',
        'value': 'com:Value/text()',
        'headerID': 'mes:ID/text()',
        'header_prepared': 'mes:Prepared/text()',
        'header_sender': 'mes:Sender/@*',
        'header_receiver': 'mes:Receiver/@*',
        'assignment_status': '@assignmentStatus',
        'error': 'mes:error/@*',
        'ref_version': '@version',
        'concept_identity': 'str:ConceptIdentity',
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
        model.DataSet: 'mes:DataSet',
        'int_str_names': './*[local-name() = $name]/@xml:lang',
        model.Representation: 'str:LocalRepresentation',
        'int_str_values': './*[local-name() = $name]/text()',
        'enumeration': 'str:Enumeration',
        'texttype': 'str:TextFormat/@textType',
        'maxlength': 'str:TextFormat/@maxLength',
        # need this? It is just a non-offset Ref
        'attr_relationship': '*/Ref/@id',
        'cat_scheme_id': '../@id'
    }

    @classmethod
    def _compile_paths(cls):
        for key, path in cls._paths.items():
            cls._paths[key] = XPath(
                path, namespaces=cls._nsmap, smart_strings=False)

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

    def dim_at_obs(self, sdmxobj):
        return self.read_as_str('dim_at_obs', sdmxobj)

    def structured_by(self, sdmxobj):
        return self.read_as_str('structured_by', sdmxobj)

    # Types for generic observations
    _ObsTuple = namedtuple_factory(
        'GenericObservation', ('key', 'value', 'attrib'))
    _SeriesObsTuple = namedtuple_factory(
        'SeriesObservation', ('dim', 'value', 'attrib'))

    def iter_generic_obs(self, sdmxobj, with_value, with_attributes):
        ObsKeyTuple = ObsAttrTuple = None
        if self.dsd:
            # this is a structure-specific dataset
            for obs in sdmxobj._elem.iterchildren('Obs'):
                # dimensions:
                obs_attrib = obs.attrib  # XML attrib
                if not ObsKeyTuple:
                    obs_key_id = [k for k in self.dim_ids if k in obs_attrib]
                    ObsKeyTuple = namedtuple_factory('ObsKey', obs_key_id)
                obs_key_values = [obs_attrib[k]
                                  for k in self.dim_ids if k in obs_attrib]
                obs_key = ObsKeyTuple._make(obs_key_values)
                obs_value = obs_attrib['OBS_VALUE'] if with_value else None
                if with_attributes:
                    if not ObsAttrTuple:
                        obs_attr_id = [
                            k for k in self.attrib_ids if k in obs_attrib]
                        ObsAttrTuple = namedtuple_factory(
                            'ObsAttributes', obs_attr_id)
                    obs_attr_values = [obs_attrib[k] for k in obs_attr_id]
                    obs_attr = ObsAttrTuple(*obs_attr_values)
                else:
                    obs_attr = None
                yield self._ObsTuple(obs_key, obs_value, obs_attr)
        else:
            # we have a generic dataset
            for obs in self._paths['generic_obs_path'](sdmxobj._elem):
                # Construct the namedtuple for the ObsKey.
                # The namedtuple class is created on first iteration.
                obs_key_values = self._paths['obs_key_values_path'](obs)
                if not ObsKeyTuple:
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
        if self.dsd:
            iter_series = sdmxobj._elem.iterchildren('Series')
        else:
            iter_series = self._paths[model.Series](sdmxobj._elem)
        for series in iter_series:
            yield model.Series(self, series, dataset=sdmxobj)

    def generic_groups(self, sdmxobj):
        if self.dsd:
            groups_iter = sdmxobj._elem.iterchildren('Group')
        else:
            groups_iter = self._paths[model.Group](sdmxobj._elem)
        for group in groups_iter:
            yield model.Group(self, group)

    def series_key(self, sdmxobj):
        if self.dsd:
            # handle structured-specific dataset
            series_attrib = sdmxobj._elem.attrib
            series_key_id, series_key_values = zip(*((k, series_attrib[k])
                                                     for k in self.dim_ids if k in series_attrib))
        else:
            # generic dataset
            series_key_id = self._paths['series_key_id_path'](sdmxobj._elem)
            series_key_values = self._paths[
                'series_key_values_path'](sdmxobj._elem)
        SeriesKeyTuple = namedtuple_factory('SeriesKey', series_key_id)
        return SeriesKeyTuple._make(series_key_values)

    def group_key(self, sdmxobj):
        if self.dsd:
            # handle structure-specific dataset
            group_attrib = sdmxobj._elem.attrib
            group_key_id, group_key_values = zip(*((k, group_attrib[k])
                                                   for k in self.dim_ids if k in group_attrib))
        else:
            # generic dataset
            group_key_id = self._paths['group_key_id_path'](sdmxobj._elem)
            group_key_values = self._paths[
                'group_key_values_path'](sdmxobj._elem)
        GroupKeyTuple = namedtuple_factory('GroupKey', group_key_id)
        return GroupKeyTuple._make(group_key_values)

    def series_attrib(self, sdmxobj):
        if self.dsd:
            # structure-specific dataset
            series_attrib = sdmxobj._elem.attrib
            attrib_l = [(k, series_attrib[k])
                        for k in self.attrib_ids if k in series_attrib]
            if attrib_l:
                attr_id, attr_values = zip(*attrib_l)
            else:
                attr_id = attr_values = []
        else:
            # generic dataset
            attr_id = self._paths['attr_id_path'](sdmxobj._elem)
            attr_values = self._paths['attr_values_path'](sdmxobj._elem)
        return namedtuple_factory('Attrib', attr_id)(*attr_values)

    dataset_attrib = series_attrib

    def iter_generic_series_obs(self, sdmxobj, with_value, with_attributes,
                                reverse_obs=False):
        ObsAttrTuple = None
        if self.dsd:
            # this is a structure-specific dataset
            for obs in sdmxobj._elem.iterchildren(reversed=reverse_obs):
                obs_attrib = obs.attrib  # XML attributes
                # dim at obs
                obs_dim = obs_attrib[self.message.data.dim_at_obs]
                obs_value = obs_attrib['OBS_VALUE'] if with_value else None
                if with_attributes:
                    if not ObsAttrTuple:
                        obs_attr_id = [
                            k for k in self.attrib_ids if k in obs_attrib]
                        ObsAttrTuple = namedtuple_factory(
                            'ObsAttributes', obs_attr_id)
                    obs_attr_values = [obs_attrib[k] for k in obs_attr_id]
                    obs_attr = ObsAttrTuple(*obs_attr_values)
                else:
                    obs_attr = None
                yield self._SeriesObsTuple(obs_dim, obs_value, obs_attr)
        else:
            # we have a generic dataset
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
