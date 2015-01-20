
    # encoding: utf-8


import pandasdmx
estat=pandasdmx.Eurostat()
m=estat.datastructure('apro_mk_cola') 
dsd=m.datastructures.aslist[0]
dim=dsd.dimensions
att=dsd.attributes
meas=dsd.measures
m2=estat.dataflows(from_file = 'pandasdmx/tests/data/demography/esms.xml')