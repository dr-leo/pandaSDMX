from pandasdmx import Request
r = Request('ESTAT')
resp = r.get(resource_type='data', agency='estat', resource_id= 'apro_mk_cola', from_file='apro_data.xml')
# Write the data to a pandas DataFrame:
data_frame = resp.write(resp.msg.data, attributes = '', asframe = True)
# With all attributes use the default value for 'attributes':
# data_frame,attributes_frame = resp.write(resp.msg.data, asframe = True)

        
        