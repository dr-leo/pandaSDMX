# encoding: utf-8

'''
.. module:: pandasdmx
    
    :synopsis: A Python- and pandas-powered client for statistical data and metadata exchange 
    For more details on SDMX see www.sdmx.org

.. :moduleauthor :: Dr. Leo fhaxbox66@gmail.com; forked from http://github.com/widukind/pysdmx
'''
  

from pandasdmx.application import app
from .agency import *

__all__ = ['ECB', 'Eurostat']

