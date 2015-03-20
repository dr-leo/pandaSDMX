from pandasdmx import Request
r = Request('ESTAT')
resp = r.get(resource_type='data', agency='estat', resource_id= 'apro_mk_cola')
# Write the data to a pandas DataFrame:
data_frame = resp.write(attributes = False, asframe = True, fromfreq=True, reverse_obs = True)
# With all attributes use the default value for 'attributes':
# data_frame,attributes_frame = resp.write(asframe = True)

        
        