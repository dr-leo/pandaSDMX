# -*- coding: utf-8 -*-

import os

import unittest

from pandasdmx.utils import namedtuple_factory
from pandasdmx.reader.sdmxml import Reader

class InseeReader(Reader):
    
    Reader._nsmap.update({
        'common': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
        'message': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
        'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
    })

class FixeReader(InseeReader):
    
    def series_key(self, sdmxobj):
        series_key_id = self._paths['series_key_id_path'](sdmxobj._elem)
        series_key_id = ",".join(series_key_id).replace("-", "_").split(",")
        series_key_values = self._paths[
            'series_key_values_path'](sdmxobj._elem)
        SeriesKeyTuple = namedtuple_factory('SeriesKey', series_key_id)
        return SeriesKeyTuple._make(series_key_values)

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

class TestInseeDataSet(unittest.TestCase):
    
    def test_bad_series_key(self):

        filepath = os.path.join(CURRENT_DIR, "data", "insee", "bug-data-namedtuple.xml")
        
        reader = InseeReader(None)
        
        with open(filepath, 'rb') as source:
            msg = reader.initialize(source)
        
            with self.assertRaises(ValueError) as err:
                list(msg.data.series)
        
        self.assertEqual(str(err.exception), "Type names and field names must be valid identifiers: 'SECT-INST'")

    def test_bad_series_key_fixe(self):
        
        filepath = os.path.join(CURRENT_DIR, "data", "insee", "bug-data-namedtuple.xml")

        reader = FixeReader(None)
        
        with open(filepath, 'rb') as source:
            msg = reader.initialize(source)
        
            count = len(list(msg.data.series))
            self.assertEqual(count, 1)

