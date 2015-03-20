from pandasdmx import Request
r = Request('ESTAT')
resp = r.get(resource_type='dataflow') 
milk_flows = [flow for flow in resp.msg.dataflows.find(
            'milk', language = 'en', field = 'name')]
c = 0
for flow in milk_flows:
    msg = r.get(resource_type = 'data', resource_id = flow, tofile = str(c) + '_EXRdata.xml')
    if msg.status_code != 200:
        print('File {}: Error code {}'.format(c, msg.status_code))
    c+=1        
        