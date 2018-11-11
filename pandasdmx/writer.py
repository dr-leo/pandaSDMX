import numpy as np
import pandas as pd

from pandasdmx.model import (
    DEFAULT_LOCALE,
    CategoryScheme,
    Codelist,
    ItemScheme,
    )
from pandasdmx.util import DictLike


class Writer:
    _write_alias = {
        CategoryScheme: ItemScheme,
        Codelist: ItemScheme,
        }

    def write(self, obj, *args, **kwargs):
        """Dispatch pattern."""
        cls = obj.__class__

        # Convenience unwrapping of objects
        # TODO consider deprecating some or all of these
        # Note: can't import/compare api.Response; would be circular
        if cls.__name__ == 'Response':
            # Handle an attempt to 'write' a pandasdmx.api.Response object
            obj = obj.msg
            cls = obj.__class__
        elif cls is 'list':
            # List of objects
            return [self.write(item, *args, **kwargs) for item in obj]
        elif cls in (dict, DictLike):
            # dict or DictLike of objects
            result = cls()
            for k, v in obj.items():
                result[k] = self.write(v, *args, **kwargs)
            return result

        method = self._write_alias.get(cls, cls).__name__.lower()
        return getattr(self, 'write_' + method)(obj, *args, **kwargs)

    def write_datamessage(self, obj, *args, **kwargs):
        if len(obj.data) == 1:
            return self.write(obj.data[0], *args, **kwargs)
        else:
            return [self.write(ds, *args, **kwargs) for ds in obj.data]

    def write_dataset(self, source=None, asframe=True, dtype=np.float64,
                      attributes='', fromfreq=False, parse_time=True):
        """Transform a :class:`pandasdmx.model.DataMessage` instance to a
        pandas DataFrame or iterator over pandas Series.

        Args:
            source(pandasdmx.model.DataMessage): a pandasdmx.model.DataSet or
                iterator of pandasdmx.model.Series

            asframe(bool): if True, merge the series of values and/or
                attributes into one or two multi-indexed pandas.DataFrame(s),
                otherwise return an iterator of pandas.Series. (default: True)

            dtype(str, np.dtype, None): datatype for values. Defaults to
                np.float64. If None, do not return the values of a series. In
                this case, attributes must not be an empty string so that some
                attribute is returned.

            attributes(str, None): string determining which attributes, if any,
                should be returned in separate series or a separate DataFrame.
                Allowed values: '', 'o', 's', 'g', 'd' or any combination
                thereof such as 'os', 'go'. Defaults to 'osgd'. Where 'o', 's',
                'g', and 'd' mean that attributes at observation, series, group
                and dataset level will be returned as members of
                per-observation namedtuples.
            fromfreq(bool): if True, extrapolate time periods from the first
                item and FREQ dimension. Default: False
            parse_time(bool): if True (default), try to generate datetime
                index, provided that dim_at_obs is 'TIME' or 'TIME_PERIOD'.
                Otherwise, ``parse_time`` is ignored. If False, always generate
                index of strings. Set it to False to increase performance and
                avoid parsing errors for exotic date-time formats unsupported
                by pandas.
        """
        # source will now be a DataSet

        # validate 'attributes'
        if attributes is None or not attributes:
            attributes = ''
        else:
            try:
                attributes = attributes.lower()
            except AttributeError:
                raise TypeError("'attributes' argument must be of type str.")
            if set(attributes) - {'o', 's', 'g', 'd'}:
                raise ValueError(
                    "'attributes' must only contain 'o', 's', 'd' or 'g'.")

        # Convert observations
        result = {}
        for observation in source.obs:
            row = {}
            if dtype:
                row['value'] = observation.value
            if attributes:
                row.update(observation.attrib)
            result[observation.key.order().get_values()] = row

        result = pd.DataFrame.from_dict(result, orient='index')

        if len(result):
            result.index.names = observation.key.order().values.keys()
            if dtype:
                result['value'] = result['value'].astype(dtype)
                if not attributes:
                    result = result['value']

        return result

    _row_content = {'codelist', 'conceptscheme', 'dataflow',
                    'categoryscheme'}

    def write_structuremessage(self, obj, rows=None, **kwargs):
        '''
        Transfform structural metadata, i.e. codelists, concept-schemes,
        lists of dataflow definitions or category-schemes from a
        :class:`pandasdmx.model.StructureMessage` instance into a pandas
        DataFrame.

        This method is called by :meth:`pandasdmx.api.Response.write`. It is
        not part of the public-facing API. Yet, certain kwargs are propagated
        from there.

        Args:
            source(pandasdmx.model.StructureMessage): a
                :class:`pandasdmx.model.StructureMessage` instance.

            rows(str): sets the desired content to be extracted from the
                StructureMessage. Must be a name of an attribute of the
                StructureMessage. The attribute must be an instance of `dict`
                whose keys are strings. These will be interpreted as ID's and
                used for the MultiIndex of the DataFrame to be returned. Values
                can be either instances of `dict` such as for codelists and
                categoryscheme, or simple nameable objects such as for
                dataflows. In the latter case, the DataFrame will have a flat
                index. (default: depends on content found in Message. Common is
                'codelist')
            columns(str, list): if str, it denotes the attribute of attributes
                of the values (nameable SDMX objects such as Code or
                ConceptScheme) that will be stored in the DataFrame. If a list,
                it must contain strings that are valid attibute values.
                Defaults to: ['name', 'description']
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
            rows = [i for i in self._row_content if hasattr(obj, i)]

        # Generate the DataFrame or -Frames and store them in a DictLike with
        # content-type names as keys
        frames = DictLike()
        for r in rows:
            frames[r] = {k: self.write(child, **kwargs) for k, child in
                         getattr(obj, r).items()}
        if return_df:
            # There is only one item. So return the only value.
            return frames.any()
        else:
            return frames

    def write_dataflowdefinition(self, obj):
        return repr(obj)

    def write_itemscheme(self, obj, locale=DEFAULT_LOCALE):
        """Convert a model.ItemScheme object to a pd.Series.

        Names from *locale* are serialized.
        """
        items = {}
        for item in obj.items:
            items[item.id] = item.name.localized_default(locale)
            # TODO return parent information

        return pd.Series(items, name=obj.id)
