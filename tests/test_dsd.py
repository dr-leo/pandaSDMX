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
        self.assertEqual(self.resp.codelist.CL_FREQ.name.en, 'FREQ')

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


class test_exr_constraints(unittest.TestCase):

    def setUp(self):
        self.ecb = Request('ecb')
        filepath = os.path.join(test_path, 'data/exr_flow.xml')
        self.resp = self.ecb.get(fromfile=filepath)

    def test_constrained_codes(self):
        m = self.resp.msg
        self.assertEqual(m._dim_ids[0], 'FREQ')
        self.assertEqual(len(m._dim_ids), 5)
        self.assertEqual(len(m._dim_ids), 5)
        self.assertEqual(len(m._dim_codes), 5)
        self.assertEqual(len(m._attr_ids), 9)
        self.assertEqual(len(m._attr_codes), 9)
        self.assertEqual(m._attr_ids[-1], 'UNIT_MULT')
        self.assertIn('5', m._attr_codes.UNIT_MULT)
        self.assertIn('W', m._dim_codes.FREQ)
        self.assertIn('W', m._dim_codes.FREQ)
        self.assertEqual(len(m._constrained_codes), 14)
        self.assertNotIn('W', m._constrained_codes.FREQ)
        key = {'FREQ': ['W']}
        self.assertTrue(m.in_codes(key))
        self.assertFalse(m.in_constraints(key, raise_error=False))
        self.assertRaises(ValueError, m.in_constraints, key)
        self.assertTrue(m.in_constraints({'CURRENCY': ['CHF']}))
        # test with invalid key
        self.assertRaises(TypeError, m._in_constraints, {'FREQ': 'A'})
        # structure writer with constraints
        out = self.resp.write()
        cl = out.codelist
        self.assertEqual(cl.shape, (3555, 2))
        # unconstrained codelists
        out = self.resp.write(constraint=False)
        cl = out.codelist
        self.assertEqual(cl.shape, (4177, 2))
