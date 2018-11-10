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
