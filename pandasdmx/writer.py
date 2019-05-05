import numpy as np
import pandas as pd

from pandasdmx.model import (
    DEFAULT_LOCALE,
    AgencyScheme,
    DataflowDefinition,
    Dimension,
    DimensionDescriptor,
    CategoryScheme,
    Codelist,
    Component,
    ConceptScheme,
    ItemScheme,
    NameableArtefact,
    Observation,
    )
from pandasdmx.util import DictLike


class Writer:
    """Converter from :mod:`model` objects to :mod:`pandas` objects."""
    # TODO support selection of language for conversion of InternationalString

    # Class → common write_*() methods
    _write_alias = {
        AgencyScheme: ItemScheme,
        CategoryScheme: ItemScheme,
        ConceptScheme: ItemScheme,
        Codelist: ItemScheme,
        DataflowDefinition: NameableArtefact,
        Dimension: Component,
        }

    def write(self, obj, *args, **kwargs):
        """Convert *obj* to pandas :mod:`pandas` objects.

        :meth:`write` implements a dispatch pattern according to the type of
        *obj*. For instance, a :class:`pandasdmx.message.DataSet` object is
        converted using :meth:`write_dataset`. See the methods named `write_*`
        for more information on their behaviour.
        """
        cls = obj.__class__

        # Convenience unwrapping of objects
        # TODO consider deprecating some or all of these
        # Note: can't import/compare api.Response; would be circular
        if cls.__name__ == 'Response':
            # Handle an attempt to 'write' a pandasdmx.api.Response object
            obj = obj.msg
            cls = obj.__class__
        elif cls is list:
            # List of objects
            if isinstance(obj[0], Observation):
                return self.write_dataset(obj, *args, **kwargs)
            else:
                return [self.write(item, *args, **kwargs) for item in obj]
        elif cls in (dict, DictLike):
            # dict or DictLike of objects
            result = dict()
            for k, v in obj.items():
                result[k] = self.write(v, *args, **kwargs)
            result = pd.Series(result)
            return result

        method = self._write_alias.get(cls, cls).__name__.lower()
        return getattr(self, 'write_' + method)(obj, *args, **kwargs)

    def write_datamessage(self, obj, *args, **kwargs):
        if len(obj.data) == 1:
            return self.write(obj.data[0], *args, **kwargs)
        else:
            return [self.write(ds, *args, **kwargs) for ds in obj.data]

    def write_dataset(self, source=None, attributes='', dtype=np.float64,
                      fromfreq=False, parse_time=True):
        """Transform a :class:`pandasdmx.model.DataMessage` instance to a
        pandas DataFrame or iterator over pandas Series.

        Parameters
        ----------
        source : :class:`pandasdmx.model.DataSet` or iterable of
                 :class:`pandasdmx.model.Observation`
        attributes : str
            Types of attributes to return with the data. A string containing
            zero or more of:

            - 'o': attributes attached to each :class`Observation`.
            - 's': attributes attached to any (0 or 1) :class:`SeriesKey`
              associated with each Observation.
            - 'g': attributes attached to any (0 or more) :class:`GroupKey`s
              associated with each Observation.
            - 'd': attributes attached to the :class:`DataSet` containing the
              Observations.

        dtype : str or np.dtype or None
            Datatype for values. If None, do not return the values of a series.
            In this case, `attributes` must not be an empty string so that some
            attribute is returned.
        fromfreq : bool
            If True, extrapolate time periods from the first item and FREQ
            dimension.
        parse_time : bool
            If True (default), try to generate datetime index, provided that
            dim_at_obs is 'TIME' or 'TIME_PERIOD'. Otherwise, ``parse_time`` is
            ignored. If False, always generate index of strings. Set it to
            False to increase performance and avoid parsing errors for exotic
            date-time formats unsupported by pandas.

        Returns
        -------
        :class:`pandas.Series` or :class:`pandas.DataFrame`
            If `attributes` is not ``''``, a :class:`pandas.DataFrame` is
            returned with ``value`` as the first column, and additional
            columns for each attribute.
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
        for observation in getattr(source, 'obs', source):
            row = {}
            if dtype:
                row['value'] = observation.value
            if attributes:
                row.update(observation.attrib)
            key = tuple(map(str, observation.key.order().get_values()))
            result[key] = row

        result = pd.DataFrame.from_dict(result, orient='index')

        if len(result):
            result.index.names = observation.key.order().values.keys()
            if dtype:
                result['value'] = result['value'].astype(dtype)
                if not attributes:
                    result = result['value']

        return result

    def write_structuremessage(self, obj, include=None, **kwargs):
        """Transform :class:`pandasdmx.message.StructureMessage` to pandas.

        Parameters
        ----------
        obj : pandasdmx.message.StructureMessage
        include : iterable of str or str, optional
            One or more of the attributes of the StructureMessage (
            'category_scheme', 'codelist', etc.) to transform.
        kwargs :
            Passed to :meth:`write` for each attribute.

        Returns
        -------
        :class:`pandasdmx.util.DictLike`
            Keys are StructureMessage attributes; values are pandas objects.
        """
        all_contents = {
            'category_scheme',
            'codelist',
            'concept_scheme',
            'constraint',
            'dataflow',
            'structure',
            'organisation_scheme',
            }

        # Handle arguments
        if include is None:
            attrs = all_contents
        else:
            attrs = set([include] if isinstance(include, str) else include)
            # Silently discard invalid names
            attrs &= all_contents
        attrs = sorted(attrs)

        result = DictLike((a, self.write(getattr(obj, a), **kwargs))
                          for a in attrs)

        return result

    def write_dimensiondescriptor(self, obj):
        return self.write(obj.components)

    def write_nameableartefact(self, obj):
        return str(obj.name)

    def write_component(self, obj):
        return str(obj.concept_identity.id)

    def write_itemscheme(self, obj, locale=DEFAULT_LOCALE):
        """Convert a model.ItemScheme object to a pd.Series.

        Names from *locale* are serialized.
        """
        items = {}
        seen = set()

        def add_item(item):
            """Recursive helper for adding items."""
            # Track seen items
            if item in seen:
                return
            else:
                seen.add(item)

            # Localized name
            row = {'name': item.name.localized_default(locale)}
            try:
                # Parent ID
                row['parent'] = item.parent.id
            except AttributeError:
                row['parent'] = ''

            items[item.id] = row

            # Add this item's children, recursively
            for child in item.child:
                add_item(child)

        for item in obj.items:
            add_item(item)

        # Convert to DataFrame
        result = pd.DataFrame.from_dict(items, orient='index', dtype=object) \
                   .rename_axis(obj.id, axis='index')

        if not result['parent'].str.len().any():
            # 'parent' column is empty; convert to pd.Series and rename
            result = result['name'].rename(obj.name.localized_default(locale))

        return result


def to_pandas(obj, *args, **kwargs):
    """Convert an SDMX-IM *obj* to a pandas object."""
    return Writer().write(obj, *args, **kwargs)
