

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
              attributes='', reverse_obs=False, fromfreq=False, parse_time=True):
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
            parse_time(bool): if True (default), try to generate datetime index, provided that
                dim_at_obs is 'TIME' or 'TIME_PERIOD'. Otherwise, ``parse_time`` is ignored. If False,
                always generate index of strings. 
                Set it to False to increase performance and avoid 
                parsing errors for exotic date-time formats unsupported by pandas.
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
                    reverse_obs, fromfreq, parse_time))
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
                                           attributes, reverse_obs, fromfreq, parse_time)

    def iter_pd_series(self, iter_series, dim_at_obs, dtype,
                       attributes, reverse_obs, fromfreq, parse_time):
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
            if parse_time and dim_at_obs == 'TIME_PERIOD':
                # Check if we can build the index based on start and freq
                # Constructing the index from the first value and FREQ should only
                # occur if 'fromfreq' is True
                # and there is a FREQ dimension at all.
                if fromfreq and 'FREQ' in series.key._fields:
                    f = series.key.FREQ
                    od0 = obs_dim[0]
                    year, subdiv = map(int, (od0[:4], od0[-1]))
                    if f == 'Q':
                        start_date = PD.datetime(year, (subdiv - 1) * 3 + 1, 1)
                        series_index = PD.period_range(
                            start=start_date, periods=l, freq='Q')
                    elif 'S' in od0:
                        # pandas cannot represent semesters as periods. So we
                        # use date_range.
                        start_date = PD.datetime(year, (subdiv - 1) * 6 + 1, 1)
                        series_index = PD.date_range(
                            start=start_date, periods=l, freq='6M')
                    else:
                        series_index = PD.period_range(start=od0, periods=l,
                                                       freq=f)
                elif 'FREQ' in series.key._fields:
                    # fromfreq is False. So generate the index from all the
                    # strings
                    f = series.key.FREQ
                    # Generate arrays for years and subdivisions (quarters or
                    # semesters
                    if f == 'Q':
                        series_index = PD.Index(PD.Period(year=int(d[:4]), quarter=int(d[-1]), freq='Q')
                                                for d in obs_dim)
                    elif f == 'H':
                        series_index = PD.Index(
                            PD.datetime(int(d[:4]), (int(d[-1]) - 1) * 6 + 1, 1) for d in obs_dim)
                    else:  # other freq such as 'A' or 'M'
                        series_index = PD.PeriodIndex(obs_dim,
                                                      freq=f)
            elif parse_time and dim_at_obs == 'TIME':
                if fromfreq and 'FREQ' in series.key._fields:
                    f = series.key.FREQ
                    series_index = PD.date_range(
                        start=obs_dim[0], periods=l, freq=f)
                else:
                    series_index = PD.DatetimeIndex(obs_dim)
            # Not a datetime or period index or don't parse it
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
