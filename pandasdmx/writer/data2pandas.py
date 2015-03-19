
'''

pandasdmx.writer.data2pandas - a pandas writer for PandaSDMX

@author: Dr. Leo
'''


import pandas as PD
import numpy as NP
from pandasdmx.writer.common import BaseWriter

    
class Writer(BaseWriter):

    def write(self, input = None, asframe = False, dtype = NP.float64, 
              attributes = ''):
        '''
        Generate pandas.Series from model.Series
        
        input: a model.DataSet or iterator of model.Series
         
        asframe: if True, merge the series of values and/or attributes 
        into one or two multi-indexed 
        pandas.DataFrame(s), otherwise return an iterator of pandas.Series.
        (default: False)
        
        dtype: datatype for values. Defaults to 'float64'
        if None, do not return the values of a series. In this case, 
        'attributes' must not be an empty string so that some attribute is returned.
        
        attributes: string determining which attributes, if any,
        should be returned in separate series or a separate DataFrame.
        'attributes' may have one of the following values: '', 'o', 's', 'g', 'd'
        or any combination thereof such as 'os', 'go'. Defaults to 'osgd'. 
        Where 'o', 's', 'g', and 'd' mean that attributes at observation,
        series, group and dataset level will be returned as members of 
        per-observation dict-likes with attribute-like access. 
        
        '''
        
        # Preparations        
        dim_at_obs = self.msg.header.dim_at_obs
        
        # validate 'attributes'
        try:
            attributes = attributes.lower()
        except AttributeError:
            raise TypeError("'attributes' argument must be of type str.")
        if set(attributes) - {'o','s','g', 'd'}: 
            raise ValueError("'attributes' must only contain 'o', 's' or 'g'.")
        
        # Allow input to be either an iterator or a model.DataSet instance
        if hasattr(input, '__iter__'): iter_series = input
        elif hasattr(input, 'series'): iter_series = input.series
        elif hasattr(input, 'data') and dim_at_obs != 'AllDimensions': iter_series = input.data.series
        
        # Is 'data' a flat dataset with just a list of obs?
        if dim_at_obs == 'AllDimensions':
            obs_zip = iter(zip(*input.data.obs()))
            dimensions = next(obs_zip)
            idx = PD.MultiIndex.from_tuples(dimensions, names = dimensions[0]._fields)
            if dtype:
                    values_series = PD.Series(next(obs_zip), dtype = dtype, index = idx)
            else: 
                values_series = None
            if  attributes:
                obs_attrib = NP.asarray(next(obs_zip), dtype = 'object')
                attrib_series = PD.Series(obs_attrib, dtype = 'object', index = idx)
            else: 
                attrib_series = None
            return values_series, attrib_series
            
        # So dataset has series:
        else:    
            if asframe:
                series_list = list(s for s in self.iter_pd_series(
                    iter_series, dim_at_obs, dtype, attributes))
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
                                                           names = level_names)
                
                         
                if dtype:
                    for s in pd_series: s.name = None
                    # Merge series into multi-indexed DataFrame and return it.
                    d_frame = PD.concat(list(pd_series), axis = 1, copy = False)
                    d_frame.columns = col_index 
                
                if attributes:
                    for s in pd_attributes: s.name = None
                    a_frame = PD.concat(pd_attributes, axis = 1, copy = False)
                    a_frame.columns = col_index
                if dtype and attributes: return d_frame, a_frame
                elif dtype: return d_frame
                else: return a_frame 
            
            # return an iterator
            else:
                return self.iter_pd_series(iter_series, dim_at_obs, dtype, 
                                           attributes)
            
        
    def iter_pd_series(self, iter_series, dim_at_obs, dtype, attributes):
        # Pre-compute some values before looping over the series
        o_in_attrib = 'o' in attributes
        s_in_attrib = 's' in attributes
        g_in_attrib = 'g' in attributes
        d_in_attrib = 'd' in attributes
        
        for series in iter_series:
            # Generate the 3 main columns: index, values and attributes
            obs_zip = iter(zip(*series.obs(dtype, attributes)))
            obs_dim = next(obs_zip)
            l = len(obs_dim)
            obs_values = NP.array(next(obs_zip), dtype = dtype)
            if attributes:
                obs_attrib = NP.array(tuple(next(obs_zip)), dtype = 'O') 
            
            # Generate the index 
            if dim_at_obs == 'TIME_PERIOD':
                # Check if we can build the index based on start and freq
                try:
                    f = series.key.FREQ
                    series_index = PD.period_range(start = obs_dim[0], periods = l, freq = f)
                except KeyError:
                    series_index = PD.PeriodIndex(obs_dim)
            elif dim_at_obs == 'TIME':
                try:
                    f = series.key.FREQ
                    series_index = PD.date_range(start = obs_dim[0], periods = l, freq = f)
                except KeyError:
                    series_index = PD.DatetimeIndex(obs_dim)
            else: series_index = PD.Index(obs_dim)
            
            if dtype:
                value_series = PD.Series(obs_values, index = series_index, name = series.key)
                
            if attributes:
                for d in obs_attrib: 
                    if not o_in_attrib: d.clear()  
                    if s_in_attrib: d.update(series.attrib) 
                    if g_in_attrib: d.update(series.group_attrib) 
                    if d_in_attrib: d.update(series.dataset.attrib) 
                attrib_series = PD.Series(obs_attrib, 
                                          index = series_index, dtype = 'object')
                
            # decide what to yield    
            if dtype and attributes: 
                yield value_series, attrib_series
            elif dtype: yield value_series
            elif attributes: yield attrib_series
            else: raise ValueError(
                "At least one of 'dtype' or 'attributes' args must be True.")
                