
    # encoding: utf-8


import pandasdmx
estat=pandasdmx.Eurostat()
m=estat.datastructure('apro_mk_cola') 
dsd=list(m.datastructures.values())[0]
dim=dsd.dimensions
freq=dim.FREQ