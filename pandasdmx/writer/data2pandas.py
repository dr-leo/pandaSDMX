

# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a writer class that writes a generic data message to
pandas dataframes or series.
'''


import pandas as PD
import numpy as NP
from pandasdmx.writer import BaseWriter


class Writer(BaseWriter):

    def write(self, source=None, asframe=True, dtype=NP.float64,
              attributes='', reverse_obs=False, fromfreq=False):
        '''Transfform a :class:`pandasdmx.model.DataMessage` instance to a pandas DataFrame
        or iterator over pandas Series.

        Args:
            source(pandasdmx.model.DataMessage): a pandasdmx.model.DataSet or iterator 
                of pandasdmx.model.Series

            asframe(bool): if True, merge the series of values and/or attributes
                into one or two multi-indexed
                pandas.DataFrame(s), otherwise return an iterator of pandas.Series.
                (default: True)

            dtype(str, NP.dtype, None): datatype for values. Defaults to NP.float64
                if None, do not return the values of a series. In this case,
                attributes must not be an empty string so that some attribute is returned.

            attributes(str, None): string determining which attributes, if any,
                should be returned in separate series or a separate DataFrame.
                Allowed values: '', 'o', 's', 'g', 'd'
                or any combination thereof such as 'os', 'go'. Defaults to 'osgd'.
                Where 'o', 's', 'g', and 'd' mean that attributes at observation,
                series, group and dataset level will be returned as members of
                per-observation dict-likes with attribute-like access.
            reverse_obs(bool): if True, return observations in 
                reverse order. Default: False
            fromfreq(bool): if True, extrapolate time periods 
                from the first item and FREQ dimension. Default: False
        '''

        # Preparations
        dim_at_obs = self.msg.header.dim_at_obs

        # validate 'attributes'
        if attributes is None or attributes == False:
            attributes = ''
        else:
            try:
                attributes = attributes.lower()
            except AttributeError:
                raise TypeError("'attributes' argument must be of type str.")
            if set(attributes) - {'o', 's', 'g', 'd'}:
                raise ValueError(
                    "'attributes' must only contain 'o', 's', 'd' or 'g'.")

        # Allow source to be either an iterator or a model.DataSet instance
        if hasattr(source, '__iter__'):
            iter_series = source
        elif hasattr(source, 'series'):
            iter_series = source.series
        elif hasattr(source, 'data') and dim_at_obs != 'AllDimensions':
            iter_series = source.data.series

        # Is 'data' a flat dataset with just a list of obs?
        if dim_at_obs == 'AllDimensions':
            obs_zip = iter(zip(*source.data.obs()))
            dimensions = next(obs_zip)
            idx = PD.MultiIndex.from_tuples(
                dimensions, names=dimensions[0]._fields)
            if dtype:
                values_series = PD.Series(
                    next(obs_zip), dtype=dtype, index=idx)
            if attributes:
                obs_attrib = NP.asarray(next(obs_zip), dtype='object')
                attrib_series = PD.Series(
                    obs_attrib, dtype='object', index=idx)
            # Decide what to return
            if dtype and attributes:
                return values_series, attrib_series
            elif dtype:
                return values_series
            elif attributes:
                return attrib_series

        # So dataset has series:
        else:
            if asframe:
                series_list = list(s for s in self.iter_pd_series(
                    iter_series, dim_at_obs, dtype, attributes,
                    reverse_obs, fromfreq))
                if dtype and attributes:
                    pd_series, pd_attributes = zip(*series_list)
                    index_source = pd_series
                elif dtype:
                    pd_series = index_source = series_list
                elif attributes:
                    pd_attributes = index_source = series_list

                # Extract dimensions
                index_tuples = list(s.name for s in index_source)
                level_names = list(index_source[0].name._fields)
                col_index = PD.MultiIndex.from_tuples(index_tuples,
                                                      names=level_names)

                if dtype:
                    for s in pd_series:
                        s.name = None
                    # Merge series into multi-indexed DataFrame and return it.
                    d_frame = PD.concat(list(pd_series), axis=1, copy=False)
                    d_frame.columns = col_index

                if attributes:
                    for s in pd_attributes:
                        s.name = None
                    a_frame = PD.concat(pd_attributes, axis=1, copy=False)
                    a_frame.columns = col_index
                # decide what to return
                if dtype and attributes:
                    return d_frame, a_frame
                elif dtype:
                    return d_frame
                else:
                    return a_frame

            # return an iterator
            else:
                return self.iter_pd_series(iter_series, dim_at_obs, dtype,
                                           attributes, reverse_obs, fromfreq)

    def iter_pd_series(self, iter_series, dim_at_obs, dtype,
                       attributes, reverse_obs, fromfreq):
        # Pre-compute some values before looping over the series
        o_in_attrib = 'o' in attributes
        s_in_attrib = 's' in attributes
        g_in_attrib = 'g' in attributes
        d_in_attrib = 'd' in attributes

        for series in iter_series:
            # Generate the 3 main columns: index, values and attributes
            obs_zip = iter(zip(*series.obs(dtype, attributes, reverse_obs)))
            obs_dim = next(obs_zip)
            l = len(obs_dim)
            obs_values = NP.array(next(obs_zip), dtype=dtype)
            if attributes:
                obs_attrib = NP.array(tuple(next(obs_zip)), dtype='O')

            # Generate the index
            if dim_at_obs == 'TIME_PERIOD':
                # Check if we can build the index based on start and freq
                # Constructing the index from the first value and FREQ should only
                # occur if 'fromfreq' is True
                # and there is a FREQ dimension at all.
                if fromfreq and 'FREQ' in series.key._fields:
                    f = series.key.FREQ
                    # Remove '-' from strings like '2014-Q1' to make pandas digest them.
                    # Use a regex instead to cover other cases such as
                    # '2014-H1' or '2014-W20'?
                    if '-Q' in obs_dim[0]:
                        obs_dim = list(obs_dim)
                        obs_dim[0] = obs_dim[0].replace('-Q', 'Q')
                    series_index = PD.period_range(
                        start=obs_dim[0], periods=l, freq=f)
                elif 'FREQ' in series.key._fields:
                    f = series.key.FREQ
                    # build the index from all observations.
                    # Remove the '-' in all dimension strings such as '2012-Q1'
                    if '-Q' in obs_dim[0]:
                        obs_dim = list(obs_dim)
                        for i in range(l):
                            obs_dim[i] = obs_dim[i].replace('-Q', 'Q')
                    series_index = PD.PeriodIndex(obs_dim,
                                                  freq=f)
            elif dim_at_obs == 'TIME':
                if fromfreq and 'FREQ' in series.key._fields:
                    f = series.key.FREQ
                    series_index = PD.date_range(
                        start=obs_dim[0], periods=l, freq=f)
                else:
                    series_index = PD.DatetimeIndex(obs_dim)
            # Not a datetime or period index
            else:
                series_index = PD.Index(obs_dim)

            if dtype:
                value_series = PD.Series(
                    obs_values, index=series_index, name=series.key)

            if attributes:
                for d in obs_attrib:
                    if not o_in_attrib:
                        d.clear()
                    if s_in_attrib:
                        d.update(series.attrib)
                    if g_in_attrib:
                        d.update(series.group_attrib)
                    if d_in_attrib:
                        d.update(series.dataset.attrib)
                attrib_series = PD.Series(obs_attrib,
                                          index=series_index, dtype='object')

            # decide what to yield
            if dtype and attributes:
                yield value_series, attrib_series
            elif dtype:
                yield value_series
            elif attributes:
                yield attrib_series
            else:
                raise ValueError(
                    "At least one of 'dtype' or 'attributes' args must be True.")
