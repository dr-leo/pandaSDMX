# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015, 2016 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a writer class that writes artefacts from a StructureMessage to
pandas dataFrames. This is useful, e.g., to visualize
codes from a codelist or concepts from a concept scheme. The writer is more general though: It can
output any collection of nameable SDMX objects.
'''

from pandasdmx.utils import DictLike
from pandasdmx.writer import BaseWriter
import pandas as PD
import numpy as NP
from itertools import chain, repeat
from operator import attrgetter


class Writer(BaseWriter):

    _row_content = {'codelist', 'conceptscheme', 'dataflow',
                    'categoryscheme'}

    def write(self, source=None, rows=None, **kwargs):
        '''
        Transfform structural metadata, i.e. codelists, concept-schemes,
        lists of dataflow definitions or category-schemes  
        from a :class:`pandasdmx.model.StructureMessage` instance into a pandas DataFrame.
        This method is called by :meth:`pandasdmx.api.Response.write` . It is not
        part of the public-facing API. Yet, certain kwargs are 
        propagated from there.

        Args:
            source(pandasdmx.model.StructureMessage): a :class:`pandasdmx.model.StructureMessage` instance.

            rows(str): sets the desired content 
                to be extracted from the StructureMessage.
                Must be a name of an attribute of the StructureMessage. The attribute must
                be an instance of `dict` whose keys are strings. These will be
                interpreted as ID's and used for the MultiIndex of the DataFrame
                to be returned. Values can be either instances of `dict` such as for codelists and categoryscheme, 
                or simple nameable objects
                such as for dataflows. In the latter case, the DataFrame will have a flat index.  
                (default: depends on content found in Message. 
                Common is 'codelist')
            columns(str, list): if str, it denotes the attribute of attributes of the
                values (nameable SDMX objects such as Code or ConceptScheme) that will be stored in the
                DataFrame. If a list, it must contain strings
                that are valid attibute values. Defaults to: ['name', 'description']
            lang(str): locale identifier. Specifies the preferred 
                language for international strings such as names.
                Default is 'en'.
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
            {r: self._make_dataframe(source, r, **kwargs) for r in rows})
        if return_df:
            # There is only one item. So return the only value.
            return frames.any()
        else:
            return frames

    def _make_dataframe(self, source, rows, constraint=None,
                        columns=['name'], lang='en'):

        def make_column(scheme, item):
            if codelist_and_dsd:
                # scheme is a (dimension or attribute, codelist) pair
                dim_attr, scheme = scheme
            # first row of a scheme, DSD-less codelist, conceptscheme etc.
            if item is None:
                # take the column attributes from the scheme itself
                item = scheme
            raw = [getattr(item, s) for s in columns]
            # Select language for international strings represented as dict
            translated = [s[lang] if lang in s
                          else (s.get('en') or ((s or None) and s.any())) for s in raw]
            # for codelists, prepend dim_or_attr flag
            if codelist_and_dsd:
                if dim_attr in dim2cl:
                    translated.insert(0, 'D')
                else:
                    translated.insert(0, 'A')
            if len(translated) > 1:
                return tuple(translated)
            else:
                return translated[0]

        def iter_keys(container):
            if codelist_and_dsd:
                if (constraint
                        and container[1] in dim2cl.values()):
                    result = (v for v in container[1].values()
                              if (v.id, container[0].id) in constraint)
                else:
                    result = container[1].values()
            else:
                result = container.values()
            return sorted(result, key=attrgetter('id'))

        def iter_schemes():
            if codelist_and_dsd:
                return chain(dim2cl.items(), attr2cl.items())
            else:
                return content.values()

        def container2id(container, item):
            if codelist_and_dsd:
                # For first index level, get dimension or attribute ID instead of
                # codelist ID
                container_id = container[0].id
                # 2nd index col: first row
                # contains the concept, all subsequent rows are codes.
                item_id = item.id
            else:
                # any other structure or codelist without DSD
                container_id = container.id
                item_id = item.id if item else None  # None in first row
            return container_id, item_id

        def row1_col2(container):
            if codelist_and_dsd:
                # return the concept of the dimension or attribute
                # instead of the (dim, codelist) pair
                return container[0].concept
            # all other cases: return None as there is nothing
            # interesting about, e.g. dataflow.
            return None

        if rows == 'codelist':
            # Assuming a msg contains only one DSD
            try:
                dsd = source.datastructure.any()
                # Relate dimensions and attributes to corresponding codelists to
                # show this relation in the resulting dataframe
                dim2cl = {d: d.local_repr.enum for d in dsd.dimensions.values()
                          if d.local_repr.enum}
                attr2cl = {a: a.local_repr.enum for a in dsd.attributes.values()
                           if a.local_repr.enum}
            except:
                dsd = None

            if constraint:
                try:
                    # use any user-provided constraint
                    constraint = constraint.constraints.any()
                except AttributeError:
                    # So the Message must containe a constraint
                    # the following is buggy: Should be linked to a dataflow,
                    # DSD or provision-agreement
                    constraint = source.constraints.any()

        # pre-compute bool value to test for DSD-related codelists
        codelist_and_dsd = (rows == 'codelist' and dsd)

        # allow `columns` arg to be a str
        if not isinstance(columns, (list, tuple)):
            columns = [columns]
        # Get the structures to be written, e.g. codelist, dataflow,
        # conceptscheme
        content = getattr(source, rows)  # 'source' is the SDMX message
        # Distinguish hierarchical content consisting of a dict of dicts, and
        # flat content consisting of a dict of atomic model instances. In the former case,
        # the resulting DataFrame will have 2 index levels.
        if isinstance(content.any(), dict):
            # generate pairs of model instances, e.g. codelist
            # and code. Their structure resembles the multi-index
            # tuples. The model instances will be replaced
            # by their id-attributes later. For now
            # we need the model instances as we want to gleen
            # from them other attributes for the dataframe columns.
            raw_tuples = chain.from_iterable(zip(
                # 1st index level eg ID of dimension
                # represented by codelist, or or ConceptScheme etc.
                repeat(container),
                # 2nd index level: first row in each codelist is the corresponding
                # container id. The following rows are item ID's. .
                chain((row1_col2(container),), iter_keys(container)))
                for container in iter_schemes())
            # Now actually generate the index and related data for the columns
            raw_idx, data = zip(*[(container2id(i, j),
                                   make_column(i, j))
                                  for i, j in raw_tuples])
            idx = PD.MultiIndex.from_tuples(raw_idx)  # set names?
        else:
            # flatt structure, e.g., dataflow definitions
            raw_tuples = sorted(content.values(), key=attrgetter('id'))
            raw_idx, data = zip(*((t.id, make_column(t, None))
                                  for t in raw_tuples))
            idx = PD.Index(raw_idx, name=rows)
        # For codelists, if there is a dsd, prepend 'dim_or_attr' as synthetic column
        # See corresponding insert in the make_columns function above
        if codelist_and_dsd:
            # make local copy to avoid side effect
            columns = columns[:]
            columns.insert(0, 'dim_or_attr')
        return PD.DataFrame(NP.array(data), index=idx, columns=columns)
