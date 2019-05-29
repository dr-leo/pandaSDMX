"""Converter from :mod:`model` and :mod:`message` to :mod:`pandas` objects."""
import numpy as np
import pandas as pd

from pandasdmx.model import (
    DEFAULT_LOCALE,
    AgencyScheme,
    DataflowDefinition,
    DataStructureDefinition,
    Dimension,
    # DimensionDescriptor,
    CategoryScheme,
    Codelist,
    Component,
    ConceptScheme,
    ItemScheme,
    NameableArtefact,
    Observation,
    SeriesKey,
    TimeDimension,
    )
from pandasdmx.util import DictLike


__all__ = ['to_pandas']


# Class → common write_*() methods
_alias = {
    DictLike: dict,
    AgencyScheme: ItemScheme,
    CategoryScheme: ItemScheme,
    ConceptScheme: ItemScheme,
    Codelist: ItemScheme,
    DataflowDefinition: NameableArtefact,
    DataStructureDefinition: NameableArtefact,
    Dimension: Component,
    TimeDimension: Component,
    }


def write(obj, *args, **kwargs):
    """Convert an SDMX *obj* to :mod:`pandas` object(s).

    :meth:`write` implements a dispatch pattern according to the type of
    *obj*. For instance, a :class:`pandasdmx.message.DataSet` object is
    converted using :meth:`write_dataset`. See the methods named `write_*`
    for more information on their behaviour.

    .. todo::
       Support selection of language for conversion of
       :class:`InternationalString`.
    """
    cls = obj.__class__
    function = 'write_' + _alias.get(cls, cls).__name__.lower()
    return globals()[function](obj, *args, **kwargs)


# Simply an alias
to_pandas = write


# Functions for Python containers
def write_list(obj, *args, **kwargs):
    """List of objects."""
    if isinstance(obj[0], Observation):
        return write_dataset(obj, *args, **kwargs)
    elif isinstance(obj[0], SeriesKey):
        return write_serieskeys(obj, *args, **kwargs)
    else:
        return [write(item, *args, **kwargs) for item in obj]


def write_dict(obj, *args, **kwargs):
    """Convert mappings.

    The values of the mapping are write()'d individually. If the resulting
    values are :class:`str` or :class:`pd.Series` *with indexes that share the
    same name*, then they are converted to a pd.Series, possibly with a
    pd.MultiIndex. Otherwise, a DictLike is returned.
    """
    result = {k: write(v, *args, **kwargs) for k, v in obj.items()}

    result_type = set(type(v) for v in result.values())

    if result_type <= {pd.Series, pd.DataFrame}:
        if (len(set(map(lambda s: s.index.name, result.values()))) == 1 and
                len(result) > 1):
            # Can safely concatenate these to a pd.MultiIndex'd Series.
            return pd.concat(result)
        else:
            # The individual pd.Series are indexed by different dimensions; do
            # not concatenate.
            return DictLike(result)
    elif result_type == {str}:
        return pd.Series(result)
    elif result_type == set():
        return pd.Series()
    else:
        raise ValueError(result_type)


# Functions for message classes
def write_response(obj, *args, **kwargs):
    """Writing a pandasdmx.api.Response → write the Response.msg."""
    return write(obj.msg, *args, **kwargs)


def write_datamessage(obj, *args, **kwargs):
    if len(obj.data) == 1:
        return write(obj.data[0], *args, **kwargs)
    else:
        return [write(ds, *args, **kwargs) for ds in obj.data]


def write_structuremessage(obj, include=None, **kwargs):
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

    result = DictLike((a, write(getattr(obj, a), **kwargs))
                      for a in attrs)

    return result


# Functions for model classes

def write_component(obj):
    return str(obj.concept_identity.id)


def write_dataset(source=None, attributes='', dtype=np.float64,
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


def write_dimensiondescriptor(obj):
    return write(obj.components)


def write_itemscheme(obj, locale=DEFAULT_LOCALE):
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


def write_nameableartefact(obj):
    return str(obj.name)


def write_serieskeys(obj):
    result = []
    for sk in obj:
        result.append({dim: kv.value for dim, kv in sk.order().values.items()})
    # TODO perhaps return as a pd.MultiIndex if that is more useful
    return pd.DataFrame(result)
