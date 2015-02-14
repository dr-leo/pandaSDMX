'''

pandasdmx.writer.pandas - a pandas writer for PandaSDMX

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

    def write(self, series, dim_at_obs, to_dataframe = False, dtype = NP.float64):
        '''
        Generate pandas.Series from model.Series
        series: an iterator of model.Series instances
        to_dataframe: if True, merge the series into a multi-indexed 
        pandas.DataFrame, otherwise return an iterator of pandas.Series.
        '''
        for s in series:
        # Generate the 3 columns (dimension, value, attrib) 
            obs_dim, obs_value, obs_attr = zip(*s.obs()) # add support for the args of Series.obs
            # Prepare dimensions and values for the series
            # if dim_at_obs in ['TIME_PERIOD', 'TIME']:
            idx = NP.array(obs_dim)
            obs_value_arr = NP.array(obs_value, dtype = dtype)
            pd_series = PD.Series(obs_value_arr, name = s.key, index = idx)
            yield pd_series
            
             
            
            
                
    def combine(self, series_list, **args):
        # Generate DataFrame    
            
        # Use the codes to generate the MultiIndex levels
        code_sets = {k : set([getattr(s.name, k) for s in series_list]) 
                     for k in series_list[0].name._fields}
            
        global_codes = {k : code_sets[k].pop() for k in code_sets 
                            if len(code_sets[k]) == 1}
        # Remove global codes as they should not lead to index levels in the DataFrame 
        for k in global_codes: code_sets.pop(k)
                
        # Sort the keys with llargest set first  
        lengths = [(len(code_sets[k]), k) for k in code_sets]
        lengths.sort(reverse = True)
        sorted_keys = [k[1] for k in lengths]        
        # Construct the multi-index from the Series.name tuples
        raw_index = [tuple([getattr(s.name, k) for k in sorted_keys]) 
                      for s in series_list]  
        column_index = PD.MultiIndex.from_tuples(raw_index, names = sorted_keys)
        df = PD.DataFrame(columns = column_index, index = series_list[0].index)
        # Add the series to the DataFrame
        for pos, s in zip(raw_index, series_list): df[pos] = s       
        
        #  Attach global metadata
        # df.meta = global_codes 
        return df
            
