
    # encoding: utf-8


import pandasdmx
estat=pandasdmx.Eurostat()
m=estat.dataflows() # get message object for the downloaded xml file 
df=m.dataflows # DictLike object of all dataflows
# find dataflows whose English name contains 'milk' or 'Milk'
# language could be omitted as it defaults to English
milk = df.findname('milk', language = 'en') 
# ID's:
print(list(milk.keys()))
# French names:
print([f.name.fr for f in milk.values()])
