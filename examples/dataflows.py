from pandasdmx import Request
r = Request('ECB')
resp = r.get(resource_type = 'dataflow' , resource_id = 'EXR', agency='ECB', to_file='ecb_dataflows.xml') 

        
        