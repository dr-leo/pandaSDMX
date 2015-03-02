from pandasdmx import Request
r = Request('ECB')
resp = r.get(resource='categoryscheme', agency = 'ECB', flow = 'MOBILE_NAVI', to_file='ecb_schemes_full.xml') 

        
        