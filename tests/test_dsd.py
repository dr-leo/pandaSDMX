# encoding: utf-8

'''


@author: Dr. Leo
'''
import pandasdmx
from pandasdmx import model

from . import MessageTest, test_data_path

import pytest


class Test_ESTAT_dsd_apro_mk_cola(MessageTest):
    path = test_data_path / 'estat'
    filename = 'apro_dsd.xml'

    def test_codelists_keys(self, msg):
        assert len(msg.codelist) == 6
        assert isinstance(msg.codelist.CL_GEO, model.Codelist)

    def test_codelist_name(self, msg):
        assert msg.codelist.CL_GEO.UK.name.en == 'United Kingdom'
        assert msg.codelist.CL_FREQ.name.en == 'FREQ'

    def test_code_cls(self, msg):
        assert isinstance(msg.codelist.CL_FREQ.D, model.Code)

    def test_writer(self, msg):
        cls_as_dfs = pandasdmx.to_pandas(msg.codelist)

        # Number of codes expected in each Codelist
        count = {
            'CL_FREQ': 6,
            'CL_GEO': 41,
            'CL_OBS_FLAG': 10,
            'CL_OBS_STATUS': 3,
            'CL_PRODMILK': 12,
            'CL_UNIT': 1,
            }

        assert all(len(df) == count[id] for id, df in cls_as_dfs.items())


class test_dsd_common(MessageTest):
    path = test_data_path / 'common'
    filename = 'common.xml'

    def test_codelists_keys(self, msg):
        assert len(msg.codelist) == 5
        assert isinstance(msg.codelist.CL_FREQ, model.Codelist)

    def test_codelist_name(self, msg):
        assert msg.codelist.CL_FREQ.D.name.en == 'Daily'

    def test_code_cls(self, msg):
        assert isinstance(msg.codelist.CL_FREQ.D, model.Code)

    def test_annotations(self, msg):
        code = self.resp.codelist.CL_FREQ.A
        anno_list = list(code.annotations)
        assert len(anno_list) == 1
        a = anno_list[0]
        assert isinstance(a, model.Annotation)
        assert a.text.en.startswith('It is')
        assert a.type == 'NOTE'


@pytest.mark.skip(reason='needs refactor')
def test_exr_constraints():
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
