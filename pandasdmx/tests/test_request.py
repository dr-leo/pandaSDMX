# encoding: utf-8

'''


@author: Dr. Leo
'''
import unittest
import pandasdmx
from pandasdmx import model, Request
from pandasdmx.utils import str_type
import os.path

pkg_path = pandasdmx.tests.__path__[0]


class Test_request(unittest.TestCase):

    def test_validate_unknown_agency(self):
        self.assertRaises(ValueError, Request, 'noagency')


if __name__ == "__main__":
    import nose
    nose.main()
