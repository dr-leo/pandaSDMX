# encoding: utf-8

'''


@author: Dr. Leo
'''
import unittest
import pandasdmx
from pandasdmx import model, Request
from pandasdmx.utils import str_type
import inspect
import os

pkg_path = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))


class Test_request(unittest.TestCase):

    def test_validate_unknown_agency(self):
        self.assertRaises(ValueError, Request, 'noagency')
