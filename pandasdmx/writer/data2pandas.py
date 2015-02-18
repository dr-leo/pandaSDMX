
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
              with_values = True, with_attrib = True):
        '''
        Generate pandas.Series from model.Series
        
        data: a model.DataSet or iterator of model.Series
         
        asframe: if True, merge the series into a multi-indexed 
        pandas.DataFrame, otherwise return an iterator of pandas.Series.
        (default: False)
        
        dtype: datatype for values. Defaults to 'float64'
        
        with_values and with_attrib: flags controlling the scope of data to be returned.
        Defaults  are True. If with_attrib is True, obs_attributes are
        returned as a pandas.DataFrame whose column index
        consists of the attribute names. The
        index is identical to the series containing the
        values.
        
        asframe: determines whether the series will be merged into a single
        DataFrame (defaults to False). If False, and both with_values
        and with_attrib are set to True, the iterator yields pairs of the form
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
            pd_series, attrib_frames = zip(*((s, a) for s, a in self.iter_pd_series(
                iter_series, dim_at_obs, dtype, with_values, with_attrib)))

            # Extract metadata
            index_tuples = list(s.name for s in pd_series)
            level_names = list(pd_series[0].name._fields)
            for s in pd_series: s.name = None
                     
            if with_values:
                # Merge series into multi-indexed DataFrame and return it.
                d_frame = PD.concat(list(pd_series), axis = 1)
                d_frame.columns = PD.MultiIndex.from_tuples(index_tuples, 
                                                       names = level_names)
            else: d_frame = None
            
            if with_attrib:
                a_frame = PD.concat(attrib_frames, axis = 1)
                # Construct the column index
                attrib_names = list(attrib_frames[0].columns.get_level_values(0))
                times = len(attrib_names) 
                upper_keys = list(chain(*(tuple(repeat(i, times)) 
                                        for i in index_tuples)))
                attrib_tuples = list(map(add, upper_keys, 
                                         ((i,) for i in 
                                          attrib_names * len(index_tuples))))
                level_names.append('ATTRIB')
                a_frame.columns = PD.MultiIndex.from_tuples(attrib_tuples, 
                                                            names = level_names)
            else: a_frame = None
            return d_frame, a_frame
        
        # return an iterator
        else:
            return self.iter_pd_series(iter_series, dim_at_obs, dtype, 
                                       with_values, with_attrib)
            
        
    def iter_pd_series(self, iter_series, dim_at_obs, dtype, with_values, with_attrib):
        for series in iter_series:
            # Generate the 3 main columns: index, values and attributes
            obs_dim, obs_values, obs_attrib = zip(*series.obs(with_values, with_attrib))
            
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
            
            if with_values:
                value_series = PD.Series(obs_values, index = series_index, name = series.key, dtype = dtype)
                
            if with_attrib:
                attrib_frame = PD.DataFrame(list(obs_attrib), columns = obs_attrib[0]._fields, index = series_index)
                
            # decide what to yield    
            if with_values and with_attrib: 
                yield value_series, attrib_frame
            elif with_values: yield value_series, None
            elif with_attrib: yield None, attrib_frame
            else: raise ValueError(
                "At least one of 'with_values' or 'with_attrib' args must be True.")
                