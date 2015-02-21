
'''

pandasdmx.writer.data2pandas - a pandas writer for PandaSDMX

@author: Dr. Leo
'''
import pdb
import pandas as PD
import numpy as NP
from pandasdmx.writer.common import BaseWriter
from itertools import chain, repeat
from operator import add

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
         
        asframe: if True, merge the series into a multi-indexed 
        pandas.DataFrame, otherwise return an iterator of pandas.Series.
        (default: False)
        
        dtype: datatype for values. Defaults to 'float64'
        
        dtype and attributes: flags controlling the scope of data to be returned.
        Defaults  are True. If attributes is True, obs_attributes are
        returned as a pandas.DataFrame whose column index
        consists of the attribute names. The
        index is identical to the series containing the
        values.
        
        asframe: determines whether the series will be merged into a single
        DataFrame (defaults to False). If False, and both dtype
        and attributes are set to True, the iterator yields pairs of the form
        (series of values, DataFrame of attributes). Otherwise,
        either Series or DataFrames are returned.
        If asframe is set to True, the resulting DataFrame
        of values will have a MultiIndex consisting of the series' keys.   
        '''
        
        # Preparations        
        dim_at_obs = self.msg.header.dim_at_obs
        
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
            obs_list = list(series.obs(dtype, attributes))
            obs_dim, obs_values, obs_attrib = zip(*obs_list)
            
            # Generate the index 
            # convert time periods to start-of-period dates (this is second-best, 
            # but there is no obvious way to convert to periods.
            if dim_at_obs == 'TIME_PERIOD':
                for i in range(len(obs_dim)):
                    try:
                        obs_dim[i][-2:] = time_spans[obs_dim[i][-2:]]
                    except KeyError: pass
            if dim_at_obs.startswith('TIME'):
                series_index = PD.to_datetime(obs_dim, unit = 'D')
            else: series_index = PD.Index(obs_dim)
            
            if dtype:
                value_series = PD.Series(obs_values, index = series_index, name = series.key, dtype = dtype)
                
            if attributes:
                attrib_series = PD.Series(list(obs_attrib), 
                                          index = series_index, dtype = 'object')
                
            # decide what to yield    
            if dtype and attributes: 
                yield value_series, attrib_series
            elif dtype: yield value_series
            elif attributes: yield attrib_series
            else: raise ValueError(
                "At least one of 'dtype' or 'attributes' args must be True.")
                