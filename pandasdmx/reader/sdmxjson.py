#! encoding: utf-8


# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014-2016 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a reader for SDMX-JSON v2.1.

'''
import json

from pandasdmx.model import (
    AllDimensions,
    AttributeValue,
    DataAttribute,
    DataMessage,
    DataSet,
    DataStructureDefinition,
    Dimension,
    DimensionDescriptor,
    Header,
    Item,
    Key,
    KeyValue,
    Observation,
    SeriesKey,
    )
from pandasdmx.reader import BaseReader


class Reader(BaseReader):
    """Read SDMXJSON 2.1 and expose it as instances from pandasdmx.model."""
    def initialize(self, source):
        # Initialize message instance
        msg = DataMessage()

        # Read JSON
        tree = json.load(source)

        # Read the header
        elem = tree['header']
        msg.header = Header(id=elem['id'], prepared=elem['prepared'],
                            sender=Item(**elem['sender']))

        # pre-fetch some structures for efficient use in series and obs
        structure = tree['structure']

        # Read dimensions and values
        dimensions = dict()
        self._dim_level = dict()
        self._dim_values = dict()
        for level_name, level in structure['dimensions'].items():
            for elem in level:
                # Create the Dimension
                d = Dimension(id=elem['id'], order=elem.get('keyPosition', -1))

                # Record the level it appears at
                self._dim_level[d] = level_name

                # Record values
                self._dim_values[d] = list()
                for value in elem.get('values', []):
                    self._dim_values[d].append(
                        KeyValue(id=d.id, value=value['id']))

                # Store
                dimensions[d.order] = d

        # Assign an order to an implicit dimension
        if -1 in dimensions:
            dimensions[len(dimensions)] = dimensions.pop(-1)

        # Prepare a dimension descriptor
        dd = DimensionDescriptor(components=[dim for _, dim in
                                             sorted(dimensions.items())])
        msg.structure = DataStructureDefinition(dimensions=dd)

        # Make a SeriesKey for Observations in this DataSet
        ds_key = SeriesKey(described_by=dd)
        for _, dim in sorted(dimensions.items()):
            if self._dim_level[dim] != 'dataSet':
                continue
            assert len(self._dim_values[dim]) == 1
            ds_key[dim.id] = self._dim_values[dim][0]

        # Determine the dimension at the observation level
        if all([level == 'observation' for level in
                self._dim_level.values()]):
            msg.observation_dimension = AllDimensions
        else:
            msg.observation_dimension = [dim for dim in dimensions.values() if
                                         self._dim_level[dim] == 'observation']

        # Read attributes and values
        self._attr_level = dict()
        self._attr_values = dict()
        for level_name, level in structure['attributes'].items():
            for attr in level:
                # Create the DataAttribute and store in the DSD
                a = DataAttribute(id=attr['id'], name=attr['name'])
                msg.structure.attributes.append(a)

                # Record the level it appears at
                self._attr_level[a] = level_name

                # Record its values
                self._attr_values[a] = list()
                for value in attr.get('values', []):
                    self._attr_values[a].append(
                        AttributeValue(value=value['name'], value_for=a))

        self.msg = msg

        # Read DataSets
        for ds in tree['dataSets']:
            msg.data.append(self.read_dataset(ds, ds_key))

        return msg

    def read_dataset(self, root, ds_key):
        ds = DataSet(action=root['action'].lower(),
                     valid_from=root.get('validFrom', None))
        for key, elem in root.get('series', {}).items():
            series_key = ds_key + self._make_key('series', key)
            ds.obs.extend(self.read_series_obs(elem, series_key))
        return ds

    def read_series_obs(self, root, series_key):
        series_attrs = self._make_attrs('series', root.get('attributes', []))
        for key, elem in root['observations'].items():
            value = elem.pop(0) if len(elem) else None
            o = Observation(series_key=series_key,
                            dimension=self._make_key('observation', key),
                            value=value,
                            attrib=series_attrs)
            o.attrib.update(self._make_attrs('observation', elem))
            yield o

    def _make_key(self, level, value):
        """Convert a string observation key to a Key().

        SDMXJSON observations have keys like '2' or '3:4', consisting of colon
        (':') separated indices. Each index refers to one of the values given
        in the DSD for an observation-level dimension.
        """
        # Instance of the proper class
        key = {
            'series': SeriesKey,
            'observation': Key,
            }[level]()
        # Iterate over key indices and the corresponding dimensions
        dims = [d for d in self.msg.structure.dimensions if
                self._dim_level[d] == level]
        for index, dim in zip(map(int, value.split(':')), dims):
            # Look up the value and assign to the Key
            # FIXME should not need to explicitly cast here
            key[dim.id] = self._dim_values[dim][index]
        return key

    def _make_attrs(self, level, values):
        """Convert integer attribute indices to an iterable of AttributeValues.

        'level' must be one of 'dataSet', 'series', or 'observation'.
        """
        attrs = [a for a in self.msg.structure.attributes if
                 self._attr_level[a] == level]
        result = {}
        for index, attr in zip(values, attrs):
            av = self._attr_values[attr][index]
            result[av.value_for] = av
        return result
