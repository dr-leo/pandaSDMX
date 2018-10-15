# encoding: utf-8

'''


@author: Dr. Leo
'''
import unittest

from pandasdmx import Request


class TestRequest(unittest.TestCase):
    def test_validate_unknown_agency(self):
        self.assertRaises(ValueError, Request, 'noagency')
