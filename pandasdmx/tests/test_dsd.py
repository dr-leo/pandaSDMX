# encoding: utf-8

'''
    

@author: Dr. Leo
'''
import unittest
import pandasdmx
from pandasdmx import model, Request
from pandasdmx.utils import str_type
import os.path

test_path = pandasdmx.tests.__path__[0]


class Test_ESTAT_dsd_apro_mk_cola(unittest.TestCase):


    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(test_path, 'data/estat/apro_dsd.xml')
        self.msg = self.estat.get(from_file = filepath)
        
    def test_codelists_keys(self):
        self.assertEqual(len(self.msg.codelists), 6)
        self.assertIsInstance(self.msg.codelists.CL_GEO, model.Codelist)
                
    def test_codelist_name(self):
        self.assertEqual(self.msg.codelists.CL_GEO.UK.name.en, 'United Kingdom')
        
        def test_code_cls(self):
            self.assertIsInstance(self.msg.codelists.CL_FREQ.D, model.Code)

    def tearDown(self): pass
        
class test_dsd_common(unittest.TestCase):
    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(test_path, 'data/common/common.xml')
        self.msg = self.estat.get(from_file = filepath)
        
    def test_codelists_keys(self):
        self.assertEqual(len(self.msg.codelists), 5)
        self.assertIsInstance(self.msg.codelists.CL_FREQ, model.Codelist)
                
    def test_codelist_name(self):
        self.assertEqual(self.msg.codelists.CL_FREQ.D.name.en, 'Daily')
        
    def test_code_cls(self):
        self.assertIsInstance(self.msg.codelists.CL_FREQ.D, model.Code)

    def test_annotations(self):
        code = self.msg.codelists.CL_FREQ.A
        anno_list = list(code.annotations)
        self.assertEqual(len(anno_list), 1)
        a = anno_list[0]
        self.assertIsInstance(a, model.Annotation)
        self.assertIsInstance(a.text.en, str_type)
        self.assertTrue(a.text.en.startswith('It is'))
        self.assertEqual(a.annotationtype, 'NOTE')
        
        
        
        

if __name__ == "__main__":
    import nose
    nose.main()