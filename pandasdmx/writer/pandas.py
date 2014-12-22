'''

pandasdmx.writer.pandas - a pandas writer for PandaSDMX

@author: Dr. Leo
'''
import pandas as PD
import numpy as NP

# Time span conversions not recognised by pandas:

time_spans = {
    'Q1' : '01-01',
    'Q2' : '04-01',
    'Q3' : '07-01',
    'Q4' : '10-01',
    'S1' : '01-01',
    'S2' : '07-01'
}

    
class PandasWriter:
    
    def transform(self, *args, **kwargs):
        """
        Transform the 5-tuple returned by self.parse into PD.Series
        """ 
        codes, raw_dates, raw_values, raw_status = args 
        if 'FREQ' in codes._fields:
            if codes.FREQ == 'A':
                freq_str = 'Y'
            else: 
                freq_str = codes.FREQ
            dates = PD.PeriodIndex(raw_dates, freq = freq_str)
        else:
            dates = PD.to_datetime(raw_dates)
        value_series = PD.TimeSeries(raw_values, index = dates, 
                    dtype = self.datatype, name = codes)
        return value_series

    
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
            
