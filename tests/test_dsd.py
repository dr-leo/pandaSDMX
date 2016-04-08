# encoding: utf-8

'''


@author: Dr. Leo
'''
import unittest
import pandasdmx
from pandasdmx import model, Request
import os.path
import inspect

test_path = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))


class Test_ESTAT_dsd_apro_mk_cola(unittest.TestCase):

    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(test_path, 'data/estat/apro_dsd.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_codelists_keys(self):
        self.assertEqual(len(self.resp.codelist), 6)
        self.assertIsInstance(self.resp.codelist.CL_GEO, model.Codelist)

    def test_codelist_name(self):
        self.assertEqual(
            self.resp.msg.codelist.CL_GEO.UK.name.en, 'United Kingdom')
        assert self.resp.codelist.CL_FREQ.name.en == 'FREQ'

        def test_code_cls(self):
            self.assertIsInstance(
                self.resp.codelist.CL_FREQ.D, model.Code)

    def test_writer(self):
        df = self.resp.write(rows='codelist')
        self.assertEqual(df.shape, (79, 2))

    def tearDown(self):
        pass


class test_dsd_common(unittest.TestCase):

    def setUp(self):
        self.estat = Request('ESTAT')
        filepath = os.path.join(test_path, 'data/common/common.xml')
        self.resp = self.estat.get(fromfile=filepath)

    def test_codelists_keys(self):
        self.assertEqual(len(self.resp.msg.codelist), 5)
        self.assertIsInstance(self.resp.msg.codelist.CL_FREQ, model.Codelist)

    def test_codelist_name(self):
        self.assertEqual(self.resp.msg.codelist.CL_FREQ.D.name.en, 'Daily')

    def test_code_cls(self):
        self.assertIsInstance(self.resp.msg.codelist.CL_FREQ.D, model.Code)

    def test_annotations(self):
        code = self.resp.codelist.CL_FREQ.A
        anno_list = list(code.annotations)
        self.assertEqual(len(anno_list), 1)
        a = anno_list[0]
        self.assertIsInstance(a, model.Annotation)
        self.assertTrue(a.text.en.startswith('It is'))
        self.assertEqual(a.annotationtype, 'NOTE')
