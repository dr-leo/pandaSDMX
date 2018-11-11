# encoding: utf-8

'''


@author: Dr. Leo
'''
import pandasdmx
from pandasdmx import model

from . import MessageTest, test_data_path


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
