Pending TODOs
-------------
In rough order of priority:

- Use requests_mock (https://requests-mock.readthedocs.io) to test the ESTAT
  zipfile mechanism for providing large datasets.
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

Using pd.DataFrame for internal storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The work in this branch handles Observations as object instances. Once the implementation is complete and fully conforms to the spec, the package might
be refactored again to use pandas objects for internal storage. See:

- pandasdmx/experimental.py for a partial mock-up of such code, and
- tests/test_experimental.py for tests.

Choosing either the current or experimental DataSet as a default should be
based on detailed performance (memory and time) evaluation under a variety of
use-cases. To that end, note that the experimental DataSet involves three conversions:

1. a reader parses the XML or JSON source, creates Observation instances, and
   adds them using DataSet.add_obs()
2. experimental.DataSet.add_obs() populates a pd.DataFrame from these
   Observations, but discards them.
3. experimental.DataSet.obs() creates new Observation instances.

For a fair comparison, the API between the readers and DataSet could be changed
to eliminate the round trip in #1/#2, but *without* sacrificing the data model
consistency provided by traitlets on Observation instances.

Optimize parsing
~~~~~~~~~~~~~~~~
The current readers implement depth-first parsing of XML or JSON SDMX messages.
This ensures the returned objects confirm rigorously to the SDMX Information
Model, but can be slow for very large messages (both Structure and Data).

There are some ways this performance could be improved:

- Create-on-access: don't immediately parse an entire document, but only as
  requested to construct other objects. This would make some internals more
  complex:

  - Observation association with GroupKeys is determined by comparing the
    Observation key with the GroupKey. In order to have a complete list of all
    Observations associated with a GroupKey, at least the dimension of each
    Observation would need to be parsed immediately.

  - In pandasdmx.sdmxml.reader, references are determined to be internal or
    external by checking against an _index of already-parsed objects. This
    index would need to represent existing-but-not-parsed objects.

- Parallelize parsing, e.g. at the level of Series or other mostly-separate
  collections of objects.
