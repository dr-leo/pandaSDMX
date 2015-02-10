# encoding: utf-8

'''
    

@author: Dr. Leo
'''
import unittest
import pandasdmx
from pandasdmx import model, Request
from pandasdmx.utils import str_type
import os.path

pkg_path = pandasdmx.tests.__path__[0]

class TestGenericFlatDataSet(unittest.TestCase):
    
    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(pkg_path, 'data/exr/ecb_exr_ng/generic/ecb_exr_ng_flat.xml')
        self.msg = self.estat.get(from_file = filepath)
        
    def test_msg_type(self):
        self.assertIsInstance(self.msg, model.GenericDataMessage)
        
    def test_header_attributes(self):
        self.assertEqual(self.msg.header.structured_by, 'STR1')
        self.assertEqual(self.msg.header.dim_at_obs, 'AllDimensions')
        
    def test_dataset_cls(self):
        self.assertIsInstance(self.msg.data, model.GenericDataSet)
        
    def test_generic_obs(self):
        data = self.msg.data
        obs_list = list(data.obs())
        self.assertEqual(len(obs_list), 12)
        o0 = obs_list[0]
        self.assertEqual(len(o0), 3)
        self.assertIsInstance(o0.key, tuple) # obs_key
        self.assertEqual(o0.key.FREQ, 'M')
        self.assertEqual(o0.key.CURRENCY, 'CHF')
        self.assertIsInstance(o0.value, str_type) # obs_value
        self.assertEqual(o0.value, '1.3413')
        self.assertIsInstance(o0.attrib, tuple)
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')
        self.assertEqual(o0.attrib.DECIMALS, '4')
        
class TestGenericSeriesDataSet(unittest.TestCase):
    
    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(pkg_path, 'data/exr/ecb_exr_ng/generic/ecb_exr_ng_ts_gf.xml')
        self.msg = self.estat.get(from_file = filepath)
        
    def test_header_attributes(self):
        self.assertEqual(self.msg.header.structured_by, 'STR1')
        self.assertEqual(self.msg.header.dim_at_obs, 'TIME_PERIOD')
        
        
    def test_dataset_cls(self):
        self.assertIsInstance(self.msg.data, model.GenericDataSet)
        
    def test_generic_obs(self):
        data = self.msg.data
        series_list = list(data.series)
        self.assertEqual(len(series_list), 4)
        s3 = series_list[3]
        self.assertIsInstance(s3, model.Series)
        self.assertIsInstance(s3.key, tuple)
        self.assertEqual(len(s3.key), 5)
        self.assertEqual(s3.key.CURRENCY, 'USD')
        self.assertEqual(s3.attrib.DECIMALS, '4')
        obs_list = list(s3.obs())
        self.assertEqual(len(obs_list), 3)
        o0 = obs_list[0]
        self.assertEqual(len(o0), 3)
        self.assertIsInstance(o0.dim, str_type) # obs_key
        self.assertEqual(o0.dim, '2010-08')
        self.assertIsInstance(o0.value, str_type) # obs_value
        self.assertEqual(o0.value, '1.2894')
        self.assertIsInstance(o0.attrib, tuple)
        self.assertEqual(o0.attrib.OBS_STATUS, 'A')
        
         
        
        
if __name__ == "__main__":
    import nose
    nose.main()