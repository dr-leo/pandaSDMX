from collections import defaultdict
from itertools import chain
from typing import Set, Union

import numpy as np
import pandas as pd

from pandasdmx import message, model
from pandasdmx.model import (
    DEFAULT_LOCALE,
    AllDimensions,
    Codelist,
    DataAttribute,
    DataSet,
    DataStructureDefinition,
    Dimension,
    DimensionComponent,
    FacetValueType as FVT,
    Item,
    Observation,
    SeriesKey,
    TimeDimension,
)
from pandasdmx.util import DictLike
from pandasdmx.writer.base import BaseWriter

#: Default return type for :func:`write_dataset` and similar methods. Either
#: 'compat' or 'rows'. See the ref:`HOWTO <howto-rtype>`.
DEFAULT_RTYPE = "rows"
# map facet value types to pandas dtypes (incomplete)
FVT_MAP = {
    FVT.string: pd.StringDtype(),
    FVT.bigInteger: pd.Int64Dtype,
    FVT.integer: pd.Int32Dtype,
    FVT.long: pd.Int32Dtype,
    FVT.short: pd.Int16Dtype,
    FVT.decimal: None,
    FVT.float: float,
    FVT.boolean: pd.BooleanDtype,
    FVT.double: np.float64,
    FVT.uri: pd.StringDtype(),
    FVT.count: pd.Int64Dtype,
    FVT.incremental: pd.Int64Dtype,
    FVT.inclusiveValueRange: pd.CategoricalDtype,
}
    
    
writer = BaseWriter("pandas")


def to_pandas(obj, *args, **kwargs):
    """Convert an SDMX *obj* to :mod:`pandas` object(s).

    See :ref:`pandasdmx.writer.pandas <writer-pandas>`.
    """
    return writer.recurse(obj, *args, **kwargs)


# Functions for Python containers
@writer
def _list(obj: list, *args, **kwargs):
    """Convert a :class:`list` of SDMX objects."""
    if isinstance(obj[0], Observation):
        return write_dataset(obj, *args, **kwargs)
    elif isinstance(obj[0], DataSet) and len(obj) == 1:
        return writer.recurse(obj[0], *args, **kwargs)
    elif isinstance(obj[0], SeriesKey):
        assert len(args) == len(kwargs) == 0
        return write_serieskeys(obj)
    else:
        return [writer.recurse(item, *args, **kwargs) for item in obj]


@writer
def _dict(obj: dict, *args, **kwargs):
    """Convert mappings."""
    result = {k: writer.recurse(v, *args, **kwargs) for k, v in obj.items()}

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


@writer
def _set(obj: set, *args, **kwargs):
    """Convert :class:`set`."""
    result = {writer.recurse(o, *args, **kwargs) for o in obj}
    return result


# Functions for message classes
@writer
def write_datamessage(obj: message.DataMessage, *args, rtype=None, **kwargs):
    """Convert :class:`.DataMessage`.

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
        return writer.recurse(obj.data[0], *args, **kwargs)
    else:
        return [writer.recurse(ds, *args, **kwargs) for ds in obj.data]


@writer
def write_structuremessage(obj: message.StructureMessage, include=None, **kwargs):
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
        attr_set = all_contents
    else:
        attr_set = set([include] if isinstance(include, str) else include)
        # Silently discard invalid names
        attr_set &= all_contents
    attrs = sorted(attr_set)

    result: DictLike[str, Union[pd.Series, pd.DataFrame]] = DictLike()
    for a in attrs:
        dl = writer.recurse(getattr(obj, a), **kwargs)
        if len(dl):
            # Only add non-empty elements
            result[a] = dl

    return result


# Functions for model classes


@writer
def _c(obj: model.Component):
    """Convert :class:`.Component`."""
    # Raises AttributeError if the concept_identity is missing
    return str(obj.concept_identity.id)  # type: ignore


@writer
def _cc(obj: model.ContentConstraint, **kwargs):
    """Convert :class:`.ContentConstraint`."""
    if len(obj.data_content_region) != 1:
        raise NotImplementedError

    return writer.recurse(obj.data_content_region[0], **kwargs)


@writer
def _cr(obj: model.CubeRegion, **kwargs):
    """Convert :class:`.CubeRegion`."""
    result: DictLike[str, pd.Series] = DictLike()
    for dim, memberselection in obj.member.items():
        result[dim.id] = pd.Series(
            [mv.value for mv in memberselection.values], name=dim.id
        )
    return result

def get_component_type(component):
    lr = component.local_representation
    try:
        if isinstance(lr.enumerated, Codelist):
            return "category"
        # Get the facet value type
        fvt = lr.non_enumerated[0].value_type
        return FVT_MAP.get(fvt) or pd.StringDtype()
    except (AttributeError, KeyError):
        return "object"
        

@writer
def write_dataset(
    obj: model.DataSet,
    attributes="",
    dtype=np.float64,
    constraint=None,
    datetime=False,
    dtypes_from_dsd=False,
    **kwargs,
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
    datetime : bool or str  or .Dimension or dict, optional
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

            Any Dimension used for the frequency specification  does not
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
    data, indices = defaultdict(list), defaultdict(list)
    for observation in getattr(obj, "obs", obj):
        # Check that the Observation is within the constraint, if any
        key = observation.key.order()
        if (not constraint) or key in constraint:
            key = tuple(map(str, key.get_values()))
            # Add value and attributes
            if dtype:
                data["value"].append(observation.value)
                indices['value'].append(key)
            if attributes and attributes != "d":
                # attributes at levels obs, series and group
                for k, v in             observation.attrib.items():
                    data[k].append(v)
                    indices[k].append(key)
            if isinstance(obj, DataSet) and attributes and "d" in attributes:
                # attributes at dataset level 
                for k, v in             obj.attrib.items():
                    data[k].append(v)
                    indices[k].append(key)

    # Check for a DSD
    dsd = kwargs.get("dsd")
    if dtypes_from_dsd and not isinstance(dsd, DataStructureDefinition):
        raise TypeError(f"If `dtypes_from_dsd` is True, \
        `dsd` must be a DataStructureDefinition object.\
        Got {type(dsd)}.")
    for col_name in data:
        if col_name == "value":
            if dtypes_from_dsd:
                dt = get_component_type(dsd.measures.get("OBS_VALUE")) 
            else:
                dt = dtype
        else: # column for an attribute
            if dtypes_from_dsd:
                dt = get_component_type(dsd.attributes.get(col_name))
            else:
                dt = "object"
        # Extract raw index tuples and values for this column
        # For dtype category, we stringify the data
        if dt == "category":
            data[col_name] = map(str, data[col_name])
        # Make pd index adding names
        idx = pd.MultiIndex.from_tuples(
            indices[col_name], names=observation.key.order().values.keys())
        # Replace raw list with pd.Series
        data[col_name] = pd.Series(data[col_name], idx, dtype=dt, name=col_name)
    # Convert to pd.DataFrame if needed
    if attributes:
        result = pd.DataFrame.from_dict(data)
    else:
        result = data["value"]

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
    df.index = pd.to_datetime(df.index, format='ISO8601')

    if param["freq"]:
        # Determine frequency string, Dimension, or Attribute
        from pandas.tseries.frequencies import to_offset

        freq = param["freq"]
        if isinstance(freq, str):
            # First, try to interpret as a pandas frequency string
            try:
                to_offset(freq)
                # Valid pandas frequency string, use as-is
            except (ValueError, KeyError):
                # Not a valid pandas frequency; try as Dimension or Attribute ID
                found = False
                for component in chain(_get_dims(), _get_attrs()):
                    if component.id == freq:
                        freq = component
                        found = True
                        break

                # No named dimension in the DSD; but perhaps on the df
                if not found:
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


@writer
def _dd(obj: model.DimensionDescriptor):
    """Convert :class:`.DimensionDescriptor`."""
    return writer.recurse(obj.components)


@writer
def write_itemscheme(obj: model.ItemScheme, locale=DEFAULT_LOCALE):
    """Convert :class:`.ItemScheme`.

    Parameters
    ----------
    locale : str, optional
        Locale for names to return.

    Returns
    -------
    pandas.Series
    """
    items = {}
    seen: Set[Item] = set()

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


@writer
def _mv(obj: model.MemberValue):
    return obj.value


@writer
def _na(obj: model.NameableArtefact):
    return str(obj.name)


def write_serieskeys(obj):
    result = []
    for sk in obj:
        result.append({dim: kv.value for dim, kv in sk.order().values.items()})
    # TODO perhaps return as a pd.MultiIndex if that is more useful
    return pd.DataFrame(result)
