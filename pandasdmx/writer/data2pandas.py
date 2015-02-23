
'''

pandasdmx.writer.data2pandas - a pandas writer for PandaSDMX

@author: Dr. Leo
'''


import pandas as PD
import numpy as NP
from pandasdmx.writer.common import BaseWriter
from pandasdmx.utils import chain_namedtuples


# Time span conversions not recognised by pandas:

time_spans = {
    'Q1' : '01-01',
    'Q2' : '04-01',
    'Q3' : '07-01',
    'Q4' : '10-01',
    'S1' : '01-01',
    'S2' : '07-01'
}

    
class Writer(BaseWriter):

    def write(self, data, asframe = False, dtype = NP.float64, 
              attributes = 'osg'):
        '''
        Generate pandas.Series from model.Series
        
        data: a model.DataSet or iterator of model.Series
         
        asframe: if True, merge the series of values and/or attributes 
        into one or two multi-indexed 
        pandas.DataFrame(s), otherwise return an iterator of pandas.Series.
        (default: False)
        
        dtype: datatype for values. Defaults to 'float64'
        if None, do not return the values of a series. In this case, 
        'attributes' must not be an empty string.
        
        attributes: string determining which attributes, if any,
        should be returned in separate series or a separate DataFrame.
        'attributes' may have one of the following values: '', 'o', 's', 'g'
        or any combination thereof such as 'os', 'go'. Defaults to 'osg'. 
        Where 'o', 's', and 'g' mean that attributes at observation,
        series, and group level will be returned as members of 
        per-observation namedtuples. 
        
        '''
        
        # Preparations        
        dim_at_obs = self.msg.header.dim_at_obs
        
        # validate 'attributes'
        try:
            attributes = attributes.lower()
        except AttributeError:
            raise TypeError("'attributes' argument must be of type str.")
        if set(attributes) - {'o','s','g'}: 
            raise ValueError("'attributes' must only contain 'o', 's' or 'g'.")
        
        # Allow data to be either an iterator or a model.DataSet instance
        if hasattr(data, '__iter__'): iter_series = data
        else: iter_series = data.series
        
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
                d_frame = PD.concat(list(pd_series), axis = 1)
                d_frame.columns = col_index 
            
            if attributes:
                for s in pd_attributes: s.name = None
                a_frame = PD.concat(pd_attributes, axis = 1)
                a_frame.columns = col_index
            if dtype and attributes: return d_frame, a_frame
            elif dtype: return d_frame
            else: return a_frame 
        
        # return an iterator
        else:
            return self.iter_pd_series(iter_series, dim_at_obs, dtype, 
                                       attributes)
            
        
    def iter_pd_series(self, iter_series, dim_at_obs, dtype, attributes):
        for series in iter_series:
            # Generate the 3 main columns: index, values and attributes
            # In case of timeseries, Reverse the order 
            # to make the index chronological
            obs_list = list(series.obs(dtype, attributes))
            if series.dataset.dim_at_obs.startswith('TIME'):
                obs_list = reversed(obs_list)
            obs_dim, obs_values, obs_attrib = zip(*obs_list)
            
            # Generate the index 
            l = len(obs_dim) # to loop over the attribute list
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
                value_series = PD.Series(obs_values, index = series_index, name = series.key, dtype = dtype)
                
            if attributes:
                # Construct the namedtuples containing the attributes
                attrib_tuples = None
                  
                if 'o' in attributes: attrib_tuples = list(obs_attrib)
                if 's' in attributes:
                    suffix = series.attrib
                    if suffix:
                        if attrib_tuples is None:
                            attrib_tuples = list(suffix for i in range(len(series_index)))
                        else:
                            for i in range(l):
                                attrib_tuples[i] = chain_namedtuples(
                                                                     attrib_tuples[i], suffix)
                if 'g' in attributes:
                    suffix = series.group_attrib
                    if suffix:
                        if attrib_tuples is None:
                            attrib_tuples = list(suffix for i in range(len(series_index)))
                        else:
                            for i in range(l):
                                attrib_tuples[i] = chain_namedtuples(
                                                                     attrib_tuples[i], suffix) 
                        
                attrib_series = PD.Series(attrib_tuples, 
                                          index = series_index, dtype = 'object')
                
            # decide what to yield    
            if dtype and attributes: 
                yield value_series, attrib_series
            elif dtype: yield value_series
            elif attributes: yield attrib_series
            else: raise ValueError(
                "At least one of 'dtype' or 'attributes' args must be True.")
                