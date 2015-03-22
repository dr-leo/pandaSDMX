# encoding: utf-8

'''
This module essentially contains :func:`get` , a
convenience function for one-off queries.  
'''
  

from pandasdmx.api import Request

__all__ = ['Request']

version = '0.2dev'

def get(agency, resource_type, resource_id = None, key = None, params = {}):
    '''
    Convenience wrapper function initializing a pandasdmx.request.Request
    client and get an SDMX resource.
    '''
    r = Request(agency) 
    return r.get(resource_type = resource_type, resource_id = resource_id, key = key, params = params)

        