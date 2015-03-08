from pandasdmx import Request
r = Request('ESTAT')
resp = r.get(resource_type = 'dataflow' , agency='ESTAT', to_file='estat_dataflows.xml') 

        
        