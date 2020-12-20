from itertools import chain

import numpy as np
import pandas as pd

from pandasdmx import model
from pandasdmx.model import (
    DEFAULT_LOCALE,
    AgencyScheme,
    AllDimensions,
    DataAttribute,
    DataflowDefinition,
    DataStructureDefinition,
    DataSet,
    Dimension,
    DimensionComponent,
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


#: Default return type for :func:`write_dataset` and similar methods. Either
#: 'compat' or 'rows'. See the ref:`HOWTO <howto-rtype>`.
DEFAULT_RTYPE = "compat"


# Class → common write_*() methods
_ALIAS = {
    DictLike: dict,
    AgencyScheme: ItemScheme,
    CategoryScheme: ItemScheme,
    ConceptScheme: ItemScheme,
    Codelist: ItemScheme,
    DataflowDefinition: NameableArtefact,
    DataStructureDefinition: NameableArtefact,
    Dimension: Component,
    TimeDimension: Component,
    model.GenericDataSet: DataSet,
    model.GenericTimeSeriesDataSet: DataSet,
    model.StructureSpecificDataSet: DataSet,
    model.StructureSpecificTimeSeriesDataSet: DataSet,
}


def write(obj, *args, **kwargs):
    """Convert an SDMX *obj* to :mod:`pandas` object(s).

    Implements a dispatch pattern according to the type of *obj*. For instance,
    a :class:`.DataSet` object is converted using :func:`.write_dataset`. See
    individual ``write_*`` methods named for more information on their
    behaviour, including accepted *args* and *kwargs*.
    """
    cls = obj.__class__
    function = "write_" + _ALIAS.get(cls, cls).__name__.lower()
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
        if (
            len(set(map(lambda s: s.index.name, result.values()))) == 1
            and len(result) > 1
        ):
            # Can safely concatenate these to a pd.MultiIndex'd Series.
            return pd.concat(result)
        else:
            # The individual pd.Series are indexed by different dimensions; do
            # not concatenate.
            return DictLike(result)
    elif result_type == {str}:
        return pd.Series(result)
    elif result_type == {DictLike}:
        return result
    elif result_type == set():
        # No results
        return pd.Series()
    else:
        raise ValueError(result_type)


def write_set(obj, *args, **kwargs):
    """Convert :class:`set`."""
    result = {write(o, *args, **kwargs) for o in obj}
    return result


# Functions for message classes
def write_datamessage(obj, *args, rtype=None, **kwargs):
    """Convert :class:`.DataMessage`.

    The data set(s) within the message are converted to pandas objects.

    Parameters
    ----------
    rtype : 'compat' or 'rows', optional
        Data type to return; default :data:`.DEFAULT_RTYPE`. See the
        :ref:`HOWTO <howto-rtype>`.
    kwargs :
        Passed to :meth:`write_dataset` for each data set.

    Returns
    -------
    :class:`pandas.Series` or :class:`pandas.DataFrame`
        if `obj` has only one data set.
    list of (:class:`pandas.Series` or :class:`pandas.DataFrame`)
        if `obj` has more than one data set.
    """
    # Pass the message's DSD to assist datetime handling
    kwargs.setdefault("dsd", obj.dataflow.structure)

    # Pass the return type and associated information
    kwargs["_rtype"] = rtype or DEFAULT_RTYPE
    if kwargs["_rtype"] == "compat":
        kwargs["_message_class"] = obj.__class__
        kwargs["_observation_dimension"] = obj.observation_dimension

    if len(obj.data) == 1:
        return write(obj.data[0], *args, **kwargs)
    else:
        return [write(ds, *args, **kwargs) for ds in obj.data]


def write_structuremessage(obj, include=None, **kwargs):
    """Convert :class:`.StructureMessage`.

    Parameters
    ----------
    obj : .StructureMessage
    include : iterable of str or str, optional
        One or more of the attributes of the StructureMessage (
        'category_scheme', 'codelist', etc.) to transform.
    kwargs :
        Passed to :meth:`write` for each attribute.

    Returns
    -------
    .DictLike
        Keys are StructureMessage attributes; values are pandas objects.
    """
    all_contents = {
        "category_scheme",
        "codelist",
        "concept_scheme",
        "constraint",
        "dataflow",
        "structure",
        "organisation_scheme",
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
    """Convert :class:`.Component`.

    The :attr:`~.Concept.id` attribute of the
    :attr:`~.Component.concept_identity` is returned.
    """
    return str(obj.concept_identity.id)


def write_contentconstraint(obj, **kwargs):
    """Convert :class:`.ContentConstraint`."""
    if len(obj.data_content_region) != 1:
        raise NotImplementedError

    return write(obj.data_content_region[0], **kwargs)


def write_cuberegion(obj, **kwargs):
    """Convert :class:`.CubeRegion`."""
    result = DictLike()
    for dim, memberselection in obj.member.items():
        result[dim] = pd.Series(
            [mv.value for mv in memberselection.values], name=dim.id
        )
    return result


def write_dataset(
    obj, attributes="", dtype=np.float64, constraint=None, datetime=False, **kwargs
):
    """Convert :class:`~.DataSet`.

    See the :ref:`walkthrough <datetime>` for examples of using the `datetime`
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
    constraint : .ContentConstraint, optional
        If given, only Observations included by the *constraint* are returned.
    datetime : bool or str or or .Dimension or dict, optional
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
    :class:`pandas.DataFrame`
        - if `attributes` is not ``''``, a data frame with one row per
          Observation, ``value`` as the first column, and additional columns
          for each attribute;
        - if `datetime` is given, various layouts as described above; or
        - if `_rtype` (passed from :func:`write_datamessage`) is 'compat',
          various layouts as described in the :ref:`HOWTO <howto-rtype>`.
    :class:`pandas.Series` with :class:`pandas.MultiIndex`
        Otherwise.
    """
    # If called directly on a DataSet (rather than a parent DataMessage),
    # cannot determine the "dimension at observation level"
    rtype = kwargs.setdefault("_rtype", "rows")

    # Validate attributes argument
    attributes = attributes or ""
    try:
        attributes = attributes.lower()
    except AttributeError:
        raise TypeError("'attributes' argument must be str")

    if rtype == "compat" and kwargs["_observation_dimension"] is not AllDimensions:
        # Cannot return attributes in this case
        attributes = ""
    elif set(attributes) - {"o", "s", "g", "d"}:
        raise ValueError(f"attributes must be in 'osgd'; got {attributes}")

    # Iterate on observations
    result = {}
    for observation in getattr(obj, "obs", obj):
        # Check that the Observation is within the constraint, if any
        key = observation.key.order()
        if constraint and key not in constraint:
            continue

        # Add value and attributes
        row = {}
        if dtype:
            row["value"] = observation.value
        if attributes:
            row.update(observation.attrib)

        result[tuple(map(str, key.get_values()))] = row

    result = pd.DataFrame.from_dict(result, orient="index")

    if len(result):
        result.index.names = observation.key.order().values.keys()
        if dtype:
            result["value"] = result["value"].astype(dtype)
            if not attributes:
                result = result["value"]

    # Reshape for compatibility with v0.9
    result, datetime, kwargs = _dataset_compat(result, datetime, kwargs)
    # Handle the datetime argument, if any
    return _maybe_convert_datetime(result, datetime, obj=obj, **kwargs)


def _dataset_compat(df, datetime, kwargs):
    """Helper for :meth:`.write_dataset` 0.9 compatibility."""
    rtype = kwargs.pop("_rtype")
    if rtype != "compat":
        return df, datetime, kwargs  # Do nothing

    # Remove compatibility arguments from kwargs
    kwargs.pop("_message_class")
    obs_dim = kwargs.pop("_observation_dimension")

    if isinstance(obs_dim, list) and len(obs_dim) == 1:
        # Unwrap a length-1 list
        obs_dim = obs_dim[0]

    if obs_dim in (AllDimensions, None):
        pass  # Do nothing
    elif isinstance(obs_dim, TimeDimension):
        # Don't modify *df*; only change arguments so that
        # _maybe_convert_datetime performs the desired changes
        if datetime is False or datetime is True:
            # Either datetime is not given, or True without specifying a
            # dimension; overwrite
            datetime = obs_dim
        elif isinstance(datetime, dict):
            # Dict argument; ensure the 'dim' key is the same as obs_dim
            if datetime.setdefault("dim", obs_dim) != obs_dim:
                msg = (
                    f"datetime={datetime} conflicts with rtype='compat' and"
                    f" {obs_dim} at observation level"
                )
                raise ValueError(msg)
        else:
            assert datetime == obs_dim, (datetime, obs_dim)
    elif isinstance(obs_dim, DimensionComponent):
        # Pivot all levels except the observation dimension
        df = df.unstack([n for n in df.index.names if n != obs_dim.id])
    else:
        # E.g. some JSON messages have two dimensions at the observation level;
        # behaviour is unspecified here, so do nothing.
        pass

    return df, datetime, kwargs


def _maybe_convert_datetime(df, arg, obj, dsd=None):
    """Helper for :meth:`.write_dataset` to handle datetime indices.

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
        param["dim"] = arg
    elif isinstance(arg, DimensionComponent):
        param["dim"] = arg.id
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

    if not param["dim"]:
        # Determine time dimension
        dims = _get_dims()
        for dim in dims:
            if isinstance(dim, TimeDimension):
                param["dim"] = dim
                break
        if not param["dim"]:
            raise ValueError(f"no TimeDimension in {dims}")

    # Unstack all but the time dimension and convert
    other_dims = list(filter(lambda d: d != param["dim"], df.index.names))
    df = df.unstack(other_dims)
    df.index = pd.to_datetime(df.index)

    if param["freq"]:
        # Determine frequency string, Dimension, or Attribute
        freq = param["freq"]
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
                raise ValueError(
                    "cannot convert to PeriodIndex with " f"non-unique freq={values}"
                )

            # Store the unique value
            freq = values.pop()

            # Remove the index level
            df.columns = df.columns.droplevel(i)
        elif isinstance(freq, DataAttribute):  # pragma: no cover
            raise NotImplementedError

        df.index = df.index.to_period(freq=freq)

    if param["axis"] in {1, "columns"}:
        # Change axis
        df = df.transpose()

    return df


def write_dimensiondescriptor(obj):
    """Convert :class:`.DimensionDescriptor`.

    The :attr:`~.DimensionDescriptor.components` of the DimensionDescriptor
    are written.
    """
    return write(obj.components)


def write_itemscheme(obj, locale=DEFAULT_LOCALE):
    """Convert :class:`.ItemScheme`.

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
        row = {"name": item.name.localized_default(locale)}
        try:
            # Parent ID
            row["parent"] = item.parent.id
        except AttributeError:
            row["parent"] = ""

        items[item.id] = row

        # Add this item's children, recursively
        for child in item.child:
            add_item(child)

    for item in obj:
        add_item(item)

    # Convert to DataFrame
    result = pd.DataFrame.from_dict(items, orient="index", dtype=object).rename_axis(
        obj.id, axis="index"
    )

    if len(result) and not result["parent"].str.len().any():
        # 'parent' column is empty; convert to pd.Series and rename
        result = result["name"].rename(obj.name.localized_default(locale))

    return result


def write_membervalue(obj):
    """Convert :class:`.MemberValue`."""
    return obj.value


def write_nameableartefact(obj):
    """Convert :class:`.NameableArtefact`.

    The :attr:`~.NameableArtefact.name` attribute of *obj* is returned.
    """
    return str(obj.name)


def write_serieskeys(obj):
    """Convert a list of :class:`.SeriesKey`."""
    result = []
    for sk in obj:
        result.append({dim: kv.value for dim, kv in sk.order().values.items()})
    # TODO perhaps return as a pd.MultiIndex if that is more useful
    return pd.DataFrame(result)
