from pandasdmx import Request
r = Request('ECB')
milk_flows = [flow
for flow in r.get(resource_type='dataflow').msg.dataflows.find('EXR')]
c = 0
for flow in milk_flows:
    msg = r.get(resource_type = 'data', resource_id = flow, tofile = str(c) + '_EXRdata.xml')
    if msg.status_code != 200:
        print('File {}: Error code {}'.format(c, msg.status_code))
    c+=1        
        