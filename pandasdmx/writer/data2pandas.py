# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a writer class that writes a generic data message to
pandas dataframes or series.
'''


from pandasdmx.writer import BaseWriter
from pandasdmx.utils import concat_namedtuples
import pandas as PD
import numpy as NP


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
                or any combination thereof such as 'os', 'go'. Defaults to ''.
                Where 'o', 's', 'g', and 'd' mean that attributes at observation,
                series, group and dataset level will be returned as members of
                per-observation namedtuples.
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
        with_obs_attr = 'o' in attributes

        # Allow source to be either an iterable or a model.DataSet instance
        if hasattr(source, '__iter__'):
            iter_series = source
        elif hasattr(source, 'series'):
            iter_series = source.series
        elif hasattr(source, 'data') and dim_at_obs != 'AllDimensions':
            iter_series = source.data.series

        # Is 'data' a flat dataset with just a list of obs?
        if dim_at_obs == 'AllDimensions':
            obs_zip = iter(
                zip(*source.data.obs(with_attributes=with_obs_attr)))
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
                    # series_list is actually a list of pairs of series
                    # containing data and metadata respectively
                    key_fields = series_list[0][0].name._fields
                    pd_series, pd_attributes = zip(*series_list)
                elif dtype:
                    key_fields = series_list[0].name._fields
                    pd_series = series_list
                elif attributes:
                    key_fields = series_list[0].name._fields
                    pd_attributes = series_list

                if dtype:
                    # Merge series into multi-indexed DataFrame and return it.
                    d_frame = PD.concat(list(pd_series), axis=1, copy=False)
                    d_frame.columns.set_names(key_fields, inplace=True)

                if attributes:
                    a_frame = PD.concat(pd_attributes, axis=1, copy=False)
                    a_frame.columns.set_names(key_fields, inplace=True)
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
        with_obs_attr = 'o' in attributes
        for series in iter_series:
            # Generate the 3 main columns: index, values and attributes
            obs_zip = list(zip(*series.obs(with_values=dtype,
                                           with_attributes=with_obs_attr, reverse_obs=reverse_obs)))
            # Are there observations at all?
            if obs_zip:
                obs_dim = obs_zip[0]
                obs_values = NP.array(obs_zip[1], dtype=dtype)
                obs_attrib = obs_zip[2]
                l = len(obs_dim)

                # Generate the index
                # Get frequency if present
                if 'FREQ' in series.key:
                    f = series.key.FREQ
                elif series.attrib and 'FREQUENCY' in series.attrib:
                    f = series.attrib.FREQUENCY
                elif 'FREQUENCY' in series.key:
                    f = series.key.FREQUENCY
                elif series.attrib and 'FREQ' in series.attrib:
                    f = series.attrib.FREQ
                else:
                    f = None

                if parse_time and dim_at_obs == 'TIME_PERIOD':
                    # Check if we can build the index based on start and freq
                    # Constructing the index from the first value and FREQ should only
                    # occur if 'fromfreq' and hence f is True
                    if fromfreq and f:  # So there is a freq and we must use it
                        series_index = PD.period_range(start=PD.Period(obs_dim[0], freq=f), periods=l,
                                                       freq=f, name=dim_at_obs)
                    else:
                        # There is no ffreq or we must not use it.
                        # So generate the index from all the obs dim values
                        series_index = PD.PeriodIndex(
                            (PD.Period(d, freq=f) for d in obs_dim), name=dim_at_obs)
                elif parse_time and dim_at_obs == 'TIME':
                    if fromfreq and f:
                        series_index = PD.date_range(
                            start=PD.datetime(obs_dim[0]), periods=l, freq=f, name=dim_at_obs)
                    else:
                        series_index = PD.DatetimeIndex(
                            (PD.datetime(d) for d in obs_dim),
                            name=dim_at_obs)
                else:
                    # Not a datetime or period index or don't parse it
                    series_index = PD.Index(obs_dim, name=dim_at_obs)

                if dtype:
                    value_series = PD.Series(
                        obs_values, index=series_index, name=series.key)

                if attributes:
                    # Assemble attributes of dataset, group and series if
                    # needed
                    gen_attrib = [attr
                                  for flag, attr in (('s', series.attrib),
                                                     ('g', series.group_attrib), ('d', series.dataset.attrib))
                                  if (flag in attributes) and attr]
                    if gen_attrib:
                        gen_attrib = concat_namedtuples(*gen_attrib)
                    else:
                        gen_attrib = None

                    if 'o' in attributes:
                        # concat with general attributes if any
                        if gen_attrib:
                            attrib_iter = (concat_namedtuples(a, gen_attrib,
                                                              name='Attrib') for a in obs_attrib)
                        else:
                            # Simply take the obs attributes
                            attrib_iter = obs_attrib
                    else:
                        # Make iterator yielding the constant general attribute set
                        # It may be None.
                        # for each obs
                        attrib_iter = (gen_attrib for d in obs_attrib)

                    attrib_series = PD.Series(attrib_iter,
                                              index=series_index, dtype='object', name=series.key)

            else:
                # There are no observations. So generate empty DataFrames
                if dtype:
                    value_series = PD.Series(name=series.key)
                if attributes:
                    attrib_series = PD.Series(name=series.key)

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
