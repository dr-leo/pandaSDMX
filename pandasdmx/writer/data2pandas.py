
'''

pandasdmx.writer.data2pandas - a pandas writer for PandaSDMX

@author: Dr. Leo
'''

import pandas as PD
import numpy as NP
from pandasdmx.writer.common import BaseWriter


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

    def write(self, data, to_dataframe = False, dtype = NP.float64, 
              with_values = True, with_attrib = True):
        '''
        Generate pandas.Series from model.Series
        
        data: a model.DataSet or iterator of model.Series
         
        to_dataframe: if True, merge the series into a multi-indexed 
        pandas.DataFrame, otherwise return an iterator of pandas.Series.
        (default: False)
        
        dtype: datatype for values. Defaults to 'float64'
        
        with_values and with_attrib: flags controlling the scope of data to be returned.
        Defaults  are True. If with_attrib is True, obs_attributes are
        returned as a pandas.DataFrame whose column index
        consists of the attribute names. The
        index is identical to the series containing the
        values.
        
        to_dataframe: determines whether the series will be merged into a single
        DataFrame (defaults to False). If False, and both with_values
        and with_attrib are set to True, the iterator yields pairs of the form
        (series of values, DataFrame of attributes). Otherwise,
        either Series or DataFrames are returned.
        If to_dataframe is set to True, the resulting DataFrame
        of values will have a MultiIndex consisting of the series' keys.   
        '''
        
        # Preparations        
        dim_at_obs = self.msg.header.dim_at_obs
        
        # Allow data to be either an iterator or a model.DataSet instance
        if hasattr(data, '__iter__'): iter_series = data
        else: iter_series = data.series
        
        if to_dataframe:
            pd_series, attrib_frames = zip(*((s, a) for s, a in self.iter_pd_series(
                iter_series, dim_at_obs, dtype, with_values, with_attrib)))
        
            if with_values:
                # Merge series into multi-indexed DataFrame and return it.
                index_tuples = list(s.name for s in pd_series)        
                column_index = PD.MultiIndex.from_tuples(index_tuples, names = index_tuples[0]._fields)
                df = PD.DataFrame(list(pd_series), columns = column_index)
            if with_attrib: pass
            if with_values and not with_attrib: return df, None
            else: raise ValueError('combination not supported')
        else:
            return self.iter_pd_series(iter_series, dim_at_obs, dtype, 
                                       with_values, with_attrib)
            
        
    def iter_pd_series(self, iter_series, dim_at_obs, dtype, with_values, with_attrib):
        for series in iter_series:
            # Generate the 3 main columns: index, values and attributes
            obs_dim, obs_values, obs_attrib = zip(*series.obs(with_values, with_attrib))#
            
            # Generate the index 
            # convert time periods to start-of-period dates (this is second-best, 
            # but there is no obvious way to convert to periods.
            if dim_at_obs == 'TIME_PERIOD':
                for i in range(len(obs_dim)):
                    try:
                        obs_dim[i][-2:] = time_spans[obs_dim[i][-2:]]
                    except KeyError: pass
            if dim_at_obs.startswith('TIME'):
                series_index = PD.to_datetime(obs_dim)
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
                