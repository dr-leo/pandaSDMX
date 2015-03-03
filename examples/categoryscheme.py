from pandasdmx import Request
r = Request('ECB')
resp = r.get(resource_type = 'categoryscheme', agency = 'ECB', resource_id = 'MOBILE_NAVI', to_file='ecb_schemes_full.xml') 

        
        