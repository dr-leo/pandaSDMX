from pandasdmx import Request
estat = Request('ESTAT')
resp = estat.get(resource_type='data', resource_id= 'apro_mk_cola')
# Write the data to a pandas DataFrame:
data_frame = resp.write(resp.msg.data, attributes = '', asframe = True)
# With all attributes use the default value for 'attributes':
data_frame,attributes_frame = resp.write(resp.msg.data, asframe = True)

        
        