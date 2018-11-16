Pending TODOs
-------------

- Refactor Request._make_key_from_series(): generate a DSD from the list of
  series keys, and then call make_cube() on that.
- Harmonize handling of API errors. Currently at least four things can happen:
  - requests.Response.raise_for_status() produces an HTTPError.
  - a 501 error gets translated to a Python NotImplementedError.
  - a message.ErrorMessage is parsed and returned.
  - some other form of return value (e.g. an HTML error page, for ABS, or a
    plain text error page, for some others) is returned which isn't parsed or
    handled; a ValueError or something else gets raised.
- pandasdmx.api.Request._resources only contains a small subset of:
  https://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1 (see "NOT
  SUPPORTED OPERATIONS")
- Get a set of API keys for testing UNESCO and encrypt them for use in CI:
  https://docs.travis-ci.com/user/encryption-keys/

Future
------
The work in this branch has Observations as object instances. Once the implementation is complete, and fully conforms to the spec, the package can be refactored again to use pandas objects for internal storage, as follows:

- Each DataSet will be a pd.DataFrame with:
  - column 'value' containing the observation value,
  - columns with values for observation-level attributes,
  - either:
    - pd.Categorical or object columns for membership in groups and series, or
    - GroupKey and SeriesKey objects stored on the DataSet, with methods (using
      pandas internals, for speed) to retrieve Observations in the group or
      series
- additional method get_obs() that can instantiate Observation objects *if
  needed*, based on the above information.

In this case:
- The 'write' observation would become mere exposure of the pandas objects,
  with minor transformations.
- Performance would likely be improved.
