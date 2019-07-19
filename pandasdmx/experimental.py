"""Experimental DataSet class using pandas for internal storage.

Currently:
- pandasdmx.model.DataSet stores a collection of Observation instances, and
  allows retrieving these directly, via their SeriesKey, or via a GroupKey,
  with or without DataAttributes attached at various levels.
- pandasdmx.writer converts these to pd.Series and pd.DataFrame objects.

This module contains an alternate, incomplete/experimental implementation, in
which Observation values, DataAttributes, and series- and group-associations
are stored internally as a pd.DataFrame. test_experimental.py verifies that
this implementation exposes the same API as the default DataSet.

"""
from typing import Text

import pandas as pd
from pandasdmx.model import (
    ActionType,
    AnnotableArtefact,
    AttributeValue,
    DataAttribute,
    DataStructureDefinition,
    Key,
    Observation,
    )
from pandasdmx.util import DictLike


class DataSet(AnnotableArtefact):
    # SDMX-IM features
    action: ActionType = None
    attrib: DictLike[str, AttributeValue] = DictLike()
    valid_from: Text = None
    structured_by: DataStructureDefinition = None

    # Internal storage: a pd.DataFrame with columns:
    # - 'value': the Observation value.
    # - ('attr_obs', *id*): value for Observation.attached_attribute[id].
    # - TODO 'series_key': integer index of the SeriesKey associated with the
    #                      Observation.
    # - TODO 'group_keys': integer indices of the GroupKey(s) associated with
    #                      the Observation.
    _data = None

    def add_obs(self, observations, series_key=None):
        """Add *observations* to a series with *series_key*."""
        if series_key:
            raise NotImplementedError

        # dict of dicts: key → {value, attributes, etc. }
        obs_dict = {}
        for obs in observations:
            # DataFrame row for this Observation
            row = {'value': obs.value}

            # Store attributes
            for attr_id, av in obs.attached_attribute.items():
                row[('attr_obs', attr_id)] = av.value

            # Store the row
            obs_dict[obs.key.order().get_values()] = row

        # Convert to pd.DataFrame. Note similarity to pandasdmx.writer
        self._data = pd.DataFrame.from_dict(obs_dict, orient='index')

        if len(obs_dict):
            self._data.index.names = obs.key.order().values.keys()

    @property
    def obs(self):
        # In pandasdmx.model.DataSet, .obs is typed as List[Observation].
        # Here, the Observations are generated on request.
        for key, data in self._data.iterrows():
            yield self._make_obs(key, data)

    def _make_obs(self, key, data):
        """Create an Observation from tuple *key* and pd.Series *data."""
        # Create the Key
        key = Key({dim: value for dim, value in
                   zip(self._data.index.names, key)})
        attrs = {}

        # Handle columns of ._data
        for col, value in data.items():
            try:
                # A tuple column label is ('attr_obs', attr_id)
                group, attr_id = col
            except ValueError:
                # Not a tuple → the 'value' column, handled below
                continue
            if group == 'attr_obs':
                # Create a DataAttribute
                attrs[attr_id] = AttributeValue(
                    value_for=DataAttribute(id=attr_id),
                    value=value)
        return Observation(dimension=key, value=data['value'],
                           attached_attribute=attrs)
