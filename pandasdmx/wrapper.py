# -*- coding: utf-8 -*-

# CHANGEME:
EURO_DATA_DIR = '/tmp'

import pandas as pd
from pandasdmx import Request as PandaSDMXRequest
import sys

class Request(PandaSDMXRequest):
    def _do_get_data(self, resource_id, key, split_by=None, counter=None):
        pars = {"resource_type"   : "data",
                "resource_id"     : resource_id,
                "key" : key}
            
        if split_by:
            if isinstance(split_by, list) or  isinstance(split_by, tuple):
                criterion = split_by[0]
                further = split_by[1:]
            else:
                criterion = split_by
                further = None
            
            values = self.get_structure(resource_id).loc[criterion].index
            dfs = []
            for value in values:
                key[criterion] = value
                # Recurse:
                a_df = self._do_get_data(resource_id, key, split_by=further)
                dfs.append(a_df)
            df = pd.concat(dfs, axis=1)
        else:
            if self._agency == 'ESTAT':
                # https://github.com/dr-leo/pandaSDMX/issues/20
                pars['params'] = {'references' : None}
            res = self.get(**pars)
            if counter:
                counter.count()
            print(pars)
            df = res.write()
        
        return df
    
    def get_data(self, resource_id, key=None, force_download=False,
                 split_by=None):
        """Download data if not already present locally"""

        try:        
            from generic_utils import Counter
            total = reduce(int.__mul__,
                           [len(req.get_structure(flow_id).loc[dim])
                            for dim in split_by])
            counter = Counter(until=total)
        except ImportError:
            counter = None

        
        if key is None:
            key = {}

        db_path = "{}/{}.hdf".format(EURO_DATA_DIR, self.agency)
        
        if isinstance(key, dict):
            str_key = self.make_key(resource_id, key)
        else:
            str_key = key
        
        db_key = "{}/{}".format(resource_id, str_key.replace('.', '_'))
        
        if not force_download:
            try:
                df = pd.read_hdf(db_path, db_key)
                return df
            except (KeyError, IOError):
                pass
        
        print("Downloading data")
        sys.stdout.flush()
        
        df = self._do_get_data(resource_id, key, split_by=split_by,
                               counter=counter)
        
        df.to_hdf(db_path, db_key)
        
        return df

    def get_structure(self, resource_id, force_download=False):
        
        db_path = "{}/{}_structure.hdf".format(EURO_DATA_DIR, self.agency)
        db_key = resource_id
        
        if not force_download:
            try:
                descriptions = pd.read_hdf(db_path, db_key)
                return descriptions
            except (KeyError, IOError):
                pass
        
        print("Downloading structure")
        sys.stdout.flush()

        labels_index = pd.MultiIndex.from_arrays([[], []],
                                                 names=['Dimension', 'Code'])
        descriptions = pd.Series(index=labels_index, name="Description")
        
        struct = self.get(resource_type="datastructure",
                          resource_id="DSD_"+resource_id)

        dimensions = struct.msg.datastructures['DSD_'+resource_id].dimensions
        
        for dim in dimensions:
            codelist = dimensions[dim].local_repr.enum
            if codelist:
                for code in codelist:
                    descriptions.loc[dim, code] = codelist[code].name['en']

        descriptions = descriptions.sort_index()
        descriptions.to_hdf(db_path, db_key)
        
        return descriptions
