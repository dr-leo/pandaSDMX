
    # encoding: utf-8


import pandasdmx
estat=pandasdmx.Request('ESTAT')
m=estat.datastructure('apro_mk_cola', to_file = 'apro.xml') 
dsd=m.datastructures.aslist[0]
dim=dsd.dimensions
att=dsd.attributes
meas=dsd.measures
# ecb=pandasdmx.Request('ECB')
# m2=ecb.datastructure('ECB_EXR1', to_file='ecb_EXR1_dsd_ref.xml')