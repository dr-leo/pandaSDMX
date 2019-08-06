import numpy as np
import pandas as pd

from pandasdmx.model import (
    DEFAULT_LOCALE,
    AgencyScheme,
    DataflowDefinition,
    DataStructureDefinition,
    DataSet,
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
    *obj*. For instance, a :class:`pandasdmx.model.DataSet` object is
    converted using :meth:`write_dataset`. See individual ``write_*`` methods
    named for more information on their behaviour, including accepted *args*
    and *kwargs*.
    """
    cls = obj.__class__
    function = 'write_' + _alias.get(cls, cls).__name__.lower()
    return globals()[function](obj, *args, **kwargs)


# Functions for Python containers
def write_list(obj, *args, **kwargs):
    """Convert a :class:`list` of SDMX objects.

    For the following *obj*, :meth:`write_list` returns :class:`pandas.Series`
    instead of a :class:`list`:

    - a list of :class:`Observation <pandasdmx.model.Observation>`:
      the Observations are written using :meth:`write_dataset`.
    - a list with only 1 :class:`DataSet <pandasdmx.model.DataSet>` (e.g. the
       :attr:`data <pandasdmx.message.DataMessage.data>` attribute of
       :class:`DataMessage <pandasdmx.message.DataMessage>`): the Series for
       the single element is returned.
    - a list of :class:`SeriesKey`: the key values (but no data) are returned.
    """
    if isinstance(obj[0], Observation):
        return write_dataset(obj, *args, **kwargs)
    elif isinstance(obj[0], DataSet) and len(obj) == 1:
        return write(obj[0], *args, **kwargs)
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
    """Convert :class:`pandasdmx.api.Response`.

    The :attr:`msg <pandasdmx.api.Response.msg>` attribute of *obj* is
    converted.
    """
    return write(obj.msg, *args, **kwargs)


def write_datamessage(obj, *args, **kwargs):
    """Convert :class:`DataMessage <pandasdmx.message.DataMessage>`."""
    if len(obj.data) == 1:
        return write(obj.data[0], *args, **kwargs)
    else:
        return [write(ds, *args, **kwargs) for ds in obj.data]


def write_structuremessage(obj, include=None, **kwargs):
    """Convert :class:`StructureMessage <pandasdmx.message.StructureMessage>`.

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

    result = DictLike()
    for a in attrs:
        dl = write(getattr(obj, a), **kwargs)
        if len(dl):
            # Only add non-empty elements
            result[a] = dl

    return result


# Functions for model classes

def write_component(obj):
    """Convert :class:`Component <pandasdmx.model.Component>`.

    The :attr:`Concept.id <pandasdmx.model.Concept.id>` attribute of the
    :attr:`Component.concept_identity
    <pandasdmx.model.Component.concept_identity>` is returned.
    """
    return str(obj.concept_identity.id)


def write_dataset(obj, attributes='', dtype=np.float64, constraint=None,
                  fromfreq=False, parse_time=True):
    """Convert :class:`DataSet <pandasdmx.model.DataSet>`.

    Parameters
    ----------
    obj : :class:`DataSet <pandasdmx.model.DataSet>` or iterable of \
          :class:`Observation <pandasdmx.model.Observation>`
    attributes : str
        Types of attributes to return with the data. A string containing
        zero or more of:

        - ``'o'``: attributes attached to each :class:`Observation
          <pandasdmx.model.Observation>` .
        - ``'s'``: attributes attached to any (0 or 1) :class:`SeriesKey
          <pandasdmx.model.SeriesKey>` associated with each Observation.
        - ``'g'``: attributes attached to any (0 or more) :class:`GroupKeys
          <pandasdmx.model.GroupKey>` associated with each Observation.
        - ``'d'``: attributes attached to the :class:`DataSet
          <pandasdmx.model.DataSet>` containing the Observations.

    dtype : str or :class:`np.dtype` or None
        Datatype for values. If None, do not return the values of a series.
        In this case, `attributes` must not be an empty string so that some
        attribute is returned.
    constraint : :class:`ContentConstraint \
                 <pandasdmx.model.ContentConstraint>` , optional
        If given, only Observations included by the *constraint* are returned.
    fromfreq : bool, optional
        If True, extrapolate time periods from the first item and FREQ
        dimension.
    parse_time : bool, optional
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

    # Iterate on observations
    result = {}
    for observation in getattr(obj, 'obs', obj):
        # Check that the Observation is within the constraint, if any
        key = observation.key.order()
        if constraint and key not in constraint:
            continue

        # Add value and attributes
        row = {}
        if dtype:
            row['value'] = observation.value
        if attributes:
            row.update(observation.attrib)

        result[tuple(map(str, key.get_values()))] = row

    result = pd.DataFrame.from_dict(result, orient='index')

    if len(result):
        result.index.names = observation.key.order().values.keys()
        if dtype:
            result['value'] = result['value'].astype(dtype)
            if not attributes:
                result = result['value']

    return result


def write_dimensiondescriptor(obj):
    """Convert :class:`DimensionDescriptor
    <pandasdmx.model.DimensionDescriptor>`.

    The :attr:`components <pandasdmx.model.DimensionDescriptor.components>` of
    the DimensionDescriptor are written.
    """
    return write(obj.components)


def write_itemscheme(obj, locale=DEFAULT_LOCALE):
    """Convert :class:`ItemScheme <pandasdmx.model.ItemScheme>`.

    Names from *locale* are serialized.

    Returns
    -------
    pandas.Series
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
    """Convert :class:`NameableArtefact <pandasdmx.model.NameableArtefact>`.

    The :attr:`name <pandasdmx.model.NameableArtefact.name>` attribute of *obj*
    is returned.
    """
    return str(obj.name)


def write_serieskeys(obj):
    """Convert a list of :class:`SeriesKey <pandasdmx.model.SeriesKey>`."""
    result = []
    for sk in obj:
        result.append({dim: kv.value for dim, kv in sk.order().values.items()})
    # TODO perhaps return as a pd.MultiIndex if that is more useful
    return pd.DataFrame(result)
