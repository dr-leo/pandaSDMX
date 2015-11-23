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

from pandasdmx.utils import DictLike
from pandasdmx.writer import BaseWriter
import pandas as PD
from itertools import chain, repeat


class Writer(BaseWriter):

    _row_content = {'codelists', 'conceptschemes', 'dataflows',
                    'categoryschemes', 'dimensions', 'attributes'}

    def write(self, source=None, rows=None, **kwargs):
        '''
        Transfform a collection of nameable SDMX objects 
        from a :class:`pandasdmx.model.StructureMessage` instance to a pandas DataFrame.

        Args:
            source(pandasdmx.model.StructureMessage): a :class:`pandasdmx.model.StructureMessage` 

            rows(str): sets the desired content 
                to be extracted from the StructureMessage.
                Must be a name of an attribute of the StructureMessage. The attribute must
                be an instance of `dict` whose keys are strings. These will be
                interpreted as ID's and used for the MultiIndex of the DataFrame
                to be returned. Values can be either instances of `dict` such as for codelists, or simple nameable objects
                such as for dataflows. In the latter case, the DataFrame will have a flat index.  
                (default: depends on content found in Message. 
                Common is 'codelists')
            columns(str, list): if str, it denotes the only attribute of the
                values (nameable SDMX objects such as Code or ConceptScheme) that will be stored in the
                DataFrame. If a list, it must contain strings
                that are valid attibute values. Defaults to: ['name', 'description']
        '''

        # Set convenient default values for args
        # is rows a string?
        if rows is not None and not isinstance(rows, (list, tuple)):
            rows = [rows]
            return_df = True
        elif isinstance(rows, (list, tuple)) and len(rows) == 1:
            return_df = True
        else:
            return_df = False
        if rows is None:
            rows = [i for i in self._row_content if hasattr(source, i)]
        # Generate the DataFrame or -Frames and store them in a DictLike with
        # content-type names as keys
        frames = DictLike(
            {r: self.make_dataframe(source, r, **kwargs) for r in rows})
        if return_df:
            # There is only one item. So return the only value.
            return frames.any()
        else:
            return frames

    def make_dataframe(self, source, rows, constraint=None,
                       dimensions_only=False, columns=['name'], lang='en'):
        def handle_language(item):
            try:
                return item[lang]
            except KeyError:
                return None
            except TypeError:
                return item

        def get_data(scheme_id, item_id):
            if item_id == '_':
                raw = [getattr(content[scheme_id], s) for s in columns]
            else:
                raw = [getattr(content[scheme_id][item_id], s)
                       for s in columns]
            # Select language for international strings represented as dict
            return tuple(map(handle_language, raw))

        def iter_keys(scheme_id):
            if rows == 'codelists' and constraint:
                try:
                    dim_id = cl2dim[scheme_id]
                    return (key for key in content[scheme_id] if (dim_id, key) in constraint)
                except KeyError:
                    pass
            return content[scheme_id]

        def iter_schemes():
            # iterate only over codelists representing dimensions?
            if rows == 'codelists' and dimensions_only:
                return (i for i in content if i in cl2dim)
            return content

        if rows == 'codelists':
            dsd = source.datastructures.any()
            # Dimensions represented by the code lists
            dimensions = [d for d in dsd.dimensions.aslist() if d.id not in
                          ['TIME', 'TIME_PERIOD']]
            # map codelist ID's to dimension names of the DSD.
            # This is needed to efficiently check for any constraint
            cl2dim = {d.local_repr.enum.id: d.id for d in dimensions}
            if constraint:
                try:
                    # use any user-provided constraint
                    constraint = constraint.constraints.any()
                except AttributeError:
                    # So the Message must containe one
                    constraint = source.constraints.any()
                # We assume that where there's a code list, a DSD is not far.

        # allow `columns` arg to be a str
        if not isinstance(columns, (list, tuple)):
            columns = [columns]

        content = getattr(source, rows)
        # Distinguish hierarchical content consisting of a dict of dicts, and
        # flat content consisting of a dict of atomic values. In the former case,
        # the resulting DataFrame will have 2 index levels.
        if isinstance(content.any(), dict):
            # generate index
            tuples = sorted(chain(*(zip(repeat(scheme_id),  # 1st level eg codelist ID
                                        iter_keys(scheme_id))  # 2nd level eg code ID's
                                    for scheme_id in iter_schemes())))  # iterate over all codelists etc.
            # insert rows to store metadata for each codelist rather than just
            # the codes.
            # first_col tracks all inserts. It serves to apply .index()
            # efficiently.
            first_col = [t[0] for t in tuples]
            for scheme_id in iter_schemes():
                i = first_col.index(scheme_id)
                tuples.insert(i, (scheme_id, '_'))
                first_col.insert(i, scheme_id)
            idx = PD.MultiIndex.from_tuples(
                tuples, names=[rows + 'ID', 'ItemID'])
            # Extract the values
            data = [get_data(*t) for t in tuples]
        else:
            # flatt structure, e.g., dataflow definitions
            keys = sorted(content.keys())
            idx = PD.Index(keys, name=rows)
            data = [get_data(t, '_') for t in keys]
        return PD.DataFrame(data, index=idx, columns=columns)
