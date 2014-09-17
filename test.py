'''
    Created on 04.09.2014

@author: Dr. Leo
'''
import unittest, imp
import pandasdmx
pandasdmx = imp.reload(pandasdmx)


class Test(unittest.TestCase):


    def setUp(self):
        self.estat = pandasdmx.client('Eurostat')
        self.ecb = pandasdmx.client('ECB')


    def tearDown(self):
        del self.estat
        del self.ecb
        


    def testEurostatFlows(self):
        db = self.estat.get_dataflows()
        cur = db.execute('SELECT * FROM SQLITE_MASTER')
        print([str(i) for i in cur.fetchall()])

    def testECBFlows(self):
        db = self.ecb.get_dataflows()
        cur = db.execute('SELECT * FROM SQLITE_MASTER')
        l=cur.fetchall()
        print([i.keys() for i in l])



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()