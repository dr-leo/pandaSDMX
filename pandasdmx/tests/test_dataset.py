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

class TestDataSet(unittest.TestCase):
    
    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(pkg_path, 'data/exr/ecb_exr_ng/generic/ecb_exr_ng_flat.xml')
        self.mess = self.estat.datastructure('something', from_file = filepath)
        
    def test_msg_type(self):
        self.assertIsInstance(self.mess, model.GenericDataMessage)
        
    def test_header_attributes(self):
        self.assertEqual(self.mess.header.structured_by, 'STR1')
        self.assertEqual(self.mess.header.dim_at_obs, 'AllDimensions')
        
    def test_dataset_cls(self):
        self.assertIsInstance(self.mess.data, model.GenericDataSet)
        
        
        
if __name__ == "__main__":
    import nose
    nose.main()