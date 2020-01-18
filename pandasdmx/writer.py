from itertools import chain

import numpy as np
import pandas as pd

from pandasdmx.model import (
    DEFAULT_LOCALE,
    AgencyScheme,
    DataAttribute,
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
    # Pass the message's DSD to assist datetime handling
    kwargs.setdefault('dsd', obj.dataflow.structure)

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
                  datetime=False, **kwargs):
    """Convert :class:`~.DataSet`.

    See the :ref:`HOWTO <howto-datetime>` for examples of using the `datetime`
    argument.

    Parameters
    ----------
    obj : :class:`~.DataSet` or iterable of :class:`~.Observation`
    attributes : str
        Types of attributes to return with the data. A string containing
        zero or more of:

        - ``'o'``: attributes attached to each :class:`~.Observation` .
        - ``'s'``: attributes attached to any (0 or 1) :class:`~.SeriesKey`
          associated with each Observation.
        - ``'g'``: attributes attached to any (0 or more) :class:`~.GroupKey`
          associated with each Observation.
        - ``'d'``: attributes attached to the :class:`~.DataSet` containing the
          Observations.

    dtype : str or :class:`numpy.dtype` or None
        Datatype for values. If None, do not return the values of a series.
        In this case, `attributes` must not be an empty string so that some
        attribute is returned.
    constraint : :class:`~.ContentConstraint` , optional
        If given, only Observations included by the *constraint* are returned.
    datetime : bool or str or or :class:`~.Dimension` or dict, optional
        If given, return a DataFrame with a :class:`~pandas.DatetimeIndex`
        or :class:`~pandas.PeriodIndex` as the index and all other dimensions
        as columns. Valid `datetime` values include:

        - :class:`bool`: if :obj:`True`, determine the time dimension
          automatically by detecting a :class:`~.TimeDimension`.
        - :class:`str`: ID of the time dimension.
        - :class:`~.Dimension`: the matching Dimension is the time dimension.
        - :class:`dict`: advanced behaviour. Keys may include:

          - **dim** (:class:`~.Dimension` or :class:`str`): the time dimension
            or its ID.
          - **axis** (`{0 or 'index', 1 or 'columns'}`): axis on which to place
            the time dimension (default: 0).
          - **freq** (:obj:`True` or :class:`str` or :class:`~.Dimension`):
            produce :class:`pandas.PeriodIndex`. If :class:`str`, the ID of a
            Dimension containing a frequency specification. If a Dimension, the
            specified dimension is used for the frequency specification.

            Any Dimension used for the frequency specification is does not
            appear in the returned DataFrame.

    Returns
    -------
    :class:`pandas.Series` or :class:`pandas.DataFrame`
        If `attributes` is not ``''``, a :class:`pandas.DataFrame` is
        returned with ``value`` as the first column, and additional
        columns for each attribute.
    """
    # Validate attributes argument
    if attributes is None or not attributes:
        attributes = ''
    else:
        try:
            attributes = attributes.lower()
        except AttributeError:
            raise TypeError("'attributes' argument must be of type str.")
        if set(attributes) - {'o', 's', 'g', 'd'}:
            raise ValueError(
                "'attributes' must only contain 'o', 's', 'd' and/or 'g'.")

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

    return _maybe_convert_datetime(result, datetime, obj=obj, **kwargs)


def _maybe_convert_datetime(df, arg, obj, dsd=None):
    """Helper for :meth:`write_dataset` to handle datetime indices.

    Parameters
    ----------
    df : pandas.DataFrame
    arg : dict
        From the `datetime` argument to :meth:`write_dataset`.
    obj :
        From the `obj` argument to :meth:`write_dataset`.
    dsd: ~.DataStructureDefinition, optional
    """
    if not arg:
        # False, None, empty dict: no datetime conversion
        return df

    # Check argument values
    param = dict(dim=None, axis=0, freq=False)
    if isinstance(arg, str):
        param['dim'] = arg
    elif isinstance(arg, Dimension):
        param['dim'] = arg.id
    elif isinstance(arg, dict):
        extra_keys = set(arg.keys()) - set(param.keys())
        if extra_keys:
            raise ValueError(extra_keys)
        param.update(arg)
    elif isinstance(arg, bool):
        pass  # True
    else:
        raise ValueError(arg)

    def _get_dims():
        """Return an appropriate list of dimensions."""
        if len(obj.structured_by.dimensions.components):
            return obj.structured_by.dimensions.components
        elif dsd:
            return dsd.dimensions.components
        else:
            return []

    def _get_attrs():
        """Return an appropriate list of attributes."""
        if len(obj.structured_by.attributes.components):
            return obj.structured_by.attributes.components
        elif dsd:
            return dsd.attributes.components
        else:
            return []

    if not param['dim']:
        # Determine time dimension
        dims = _get_dims()
        for dim in dims:
            if isinstance(dim, TimeDimension):
                param['dim'] = dim
                break
        if not param['dim']:
            raise ValueError(f'no TimeDimension in {dims}')

    # Unstack all but the time dimension and convert
    other_dims = list(filter(lambda d: d != param['dim'], df.index.names))
    df = df.unstack(other_dims)
    df.index = pd.to_datetime(df.index)

    if param['freq']:
        # Determine frequency string, Dimension, or Attribute
        freq = param['freq']
        if isinstance(freq, str) and freq not in pd.offsets.prefix_mapping:
            # ID of a Dimension or Attribute
            for component in chain(_get_dims(), _get_attrs()):
                if component.id == freq:
                    freq = component
                    break

            # No named dimension in the DSD; but perhaps on the df
            if isinstance(freq, str):
                if freq in df.columns.names:
                    freq = Dimension(id=freq)
                else:
                    raise ValueError(freq)

        if isinstance(freq, Dimension):
            # Retrieve Dimension values from pd.MultiIndex level
            level = freq.id
            i = df.columns.names.index(level)
            values = set(df.columns.levels[i])

            if len(values) > 1:
                values = sorted(values)
                raise ValueError('cannot convert to PeriodIndex with '
                                 f'non-unique freq={values}')

            # Store the unique value
            freq = values.pop()

            # Remove the index level
            df.columns = df.columns.droplevel(i)
        elif isinstance(freq, DataAttribute):  # pragma: no cover
            raise NotImplementedError

        df.index = df.index.to_period(freq=freq)

    if param['axis'] in {1, 'columns'}:
        # Change axis
        df = df.transpose()

    return df


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

    for item in obj:
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
