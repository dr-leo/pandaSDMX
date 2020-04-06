import pandasdmx as sdmx
from pandasdmx import model

from . import MessageTest
from .data import specimen

import pytest


class Test_ESTAT_dsd_apro_mk_cola(MessageTest):
    path = MessageTest.path / 'ESTAT'
    filename = 'apro_mk_cola-structure.xml'

    def test_codelists_keys(self, msg):
        assert len(msg.codelist) == 6
        assert isinstance(msg.codelist.CL_GEO, model.Codelist)

    def test_codelist_name(self, msg):
        assert msg.codelist.CL_GEO.UK.name.en == 'United Kingdom'
        assert msg.codelist.CL_FREQ.name.en == 'FREQ'

    def test_code_cls(self, msg):
        assert isinstance(msg.codelist.CL_FREQ.D, model.Code)

    def test_writer(self, msg):
        cls_as_dfs = sdmx.to_pandas(msg.codelist)

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

    def test_urn(self, msg):
        """https://github.com/dr-leo/pandaSDMX/issue/154."""
        expected = ('urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure='
                    'ESTAT:DSD_apro_mk_cola(1.0)')

        # URN is parsed
        assert msg.structure.DSD_apro_mk_cola.urn == expected


class TestDSDCommon(MessageTest):
    path = MessageTest.path / 'SGR'
    filename = 'common-structure.xml'

    def test_codelists_keys(self, msg):
        assert len(msg.codelist) == 5
        assert isinstance(msg.codelist.CL_FREQ, model.Codelist)

    def test_codelist_name(self, msg):
        assert msg.codelist.CL_FREQ.D.name.en == 'Daily'

    def test_code_cls(self, msg):
        assert isinstance(msg.codelist.CL_FREQ.D, model.Code)

    def test_annotations(self, msg):
        code = msg.codelist.CL_FREQ.A
        anno_list = list(code.annotations)
        assert len(anno_list) == 1
        a = anno_list[0]
        assert isinstance(a, model.Annotation)
        assert a.text.en.startswith('It is')
        assert a.type == 'NOTE'


class TestECB_EXR1(MessageTest):
    path = MessageTest.path / 'ECB_EXR' / '1'
    filename = 'structure.xml'

    def test_uri(self, msg):
        """https://github.com/dr-leo/pandaSDMX/issue/154."""
        expected = 'https://www.ecb.europa.eu/vocabulary/stats/exr/1'
        # URI is parsed
        assert msg.structure['ECB_EXR1'].uri == expected


def test_exr_constraints():
    with specimen('1/structure-full.xml') as f:
        m = sdmx.read_sdmx(f)
    ECB_EXR1 = m.structure['ECB_EXR1']

    # Test DimensionDescriptor
    dd = ECB_EXR1.dimensions

    # Correct order
    assert dd[0].id == 'FREQ'

    # Correct number of dimensions
    assert len(dd.components) == 6

    # Dimensions can be retrieved by name; membership can be tested
    assert 'W' in dd.get('FREQ')

    # Similar tests for AttributeDescriptor
    ad = ECB_EXR1.attributes
    assert len(ad.components) == 24
    assert ad[-1].id == 'UNIT_MULT'
    assert '5' in ad.get('UNIT_MULT')

    pytest.xfail('constrained codes not implemented')  # TODO
    assert len(m._constrained_codes), 14

    assert 'W' not in m._constrained_codes.FREQ

    key = {'FREQ': ['W']}

    assert m.in_codes(key)

    assert not m.in_constraints(key, raise_error=False)

    with pytest.raises(ValueError):
        m.in_constraints(key)

    assert m.in_constraints({'CURRENCY': ['CHF']})

    # test with invalid key
    with pytest.raises(TypeError):
        m._in_constraints({'FREQ': 'A'})

    # structure writer with constraints
    out = sdmx.to_pandas(m)
    cl = out.codelist
    assert cl.shape == (3555, 2)

    # unconstrained codelists
    out = sdmx.to_pandas(m, constraint=False)
    cl = out.codelist
    assert cl.shape, (4177, 2)
