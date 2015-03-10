from pandasdmx import Request
r = Request('ESTAT')
resp = r.get(resource_type = 'dataflow' , to_file='ilo_dataflows.xml') 

        
        