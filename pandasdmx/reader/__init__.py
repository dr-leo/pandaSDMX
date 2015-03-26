# encoding: utf-8
'''
    This module contains the base class for readers.

'''




class BaseReader:
    
    def __init__(self, request, **kwargs):
        self.request = request
        
    
    def initialize(self, source): raise NotImplemented
    
