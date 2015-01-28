# encoding: utf-8

'''
    Created on 04.09.2014

@author: Dr. Leo
'''
import unittest, imp
import pandasdmx



class Test_DSD(unittest.TestCase):


    def setUp(self):
        self.estat = pandasdmx.request.Request('ESTAT')
        self.mess = self.estat.datastructure('dsd_apro_mk_cola')
        
    def test_codelists_keys(self):
        self.assertEqual(len(self.mess.codelists), 6)
        
    def test_codelist_name(self):
        self.assertEqual(self.mess.codelists.CL_GEO.UK.name.en, 'United Kingdom')
        


    def tearDown(self): pass
        


    def testEurostatFlows(self):
        db = self.estat.get_dataflows()
        cur = db.execute('SELECT * FROM SQLITE_MASTER')
        print([str(i) for i in cur.fetchall()])



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()