# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a writer class that writes artefacts from a StructureMessage to
pandas dataFrames. This is useful, e.g., to visualize
codes from a codelist or concepts from a concept scheme. The writer is more general though: It can
output any collection of nameable SDMX objects.
'''


from pandasdmx.writer import BaseWriter
import pandas as PD
from itertools import chain, repeat


class Writer(BaseWriter):

    def write(self, source=None, name='codelists', attrib=['name'], lang='en'):
        '''
        Transfform a collection of nameable SDMX objects 
        from a :class:`pandasdmx.model.StructureMessage` instance to a pandas DataFrame.

        Args:
            source(pandasdmx.model.StructureMessage): a :class:`pandasdmx.model.StructureMessage` 

            name(str): name of an attribute of the StructureMessage. The attribute must
                be an instance of `dict` whose keys are strings. These will be
                interpreted as ID's and used for the MultiIndex of the DataFrame
                to be returned. Values can be either instances of `dict` such as for codelists, or simple nameable objects
                such as for dataflows. In the latter case, the DataFrame will have a flat index.  
                (default: 'codelists')
            attrib(str, list): if str, it denotes the only attribute of the
                values (nameable SDMX objects such as Code or ConceptScheme) that will be stored in the
                DataFrame. If a list, it must contain strings
                that are valid attibute values. Defaults to: ['name', 'description']
        '''
        def handle_language(item):
            try:
                return item[lang]
            except KeyError:
                return None
            except TypeError:
                return item

        def get_data(scheme_id, item_id):
            if item_id == '_':
                raw = [getattr(content[scheme_id], s) for s in attrib]
            else:
                raw = [getattr(content[scheme_id][item_id], s) for s in attrib]
            # Select language for international strings represented as dict
            return tuple(map(handle_language, raw))

        if type(attrib) not in [list, tuple]:
            attrib = [attrib]
        content = getattr(source, name)
        if name == 'dataflows':
            idx = PD.Index(sorted(content.keys()), name=name)
            data = [getattr(content[i], attrib[0])[lang] for i in idx]
        else:
            # generate index
            tuples = sorted(chain(*(zip(repeat(scheme_id),  # 1st level eg codelist ID
                                        content[scheme_id].keys())  # 2nd level eg code ID's
                                    for scheme_id in content)))  # iterate over all codelists etc.
            # insert rows to store metadata for each codelist rather than just
            # the codes
            first_col = [t[0] for t in tuples]
            for scheme_id in content:
                i = first_col.index(scheme_id)
                tuples.insert(i, (scheme_id, '_'))
                first_col.insert(i, scheme_id)
            idx = PD.MultiIndex.from_tuples(
                tuples, names=[name + 'ID', 'ItemID'])
            # Extract the values
            data = [get_data(*t) for t in tuples]
        # Generate pandas DataFrame
        return PD.DataFrame(data, index=idx, columns=attrib)
