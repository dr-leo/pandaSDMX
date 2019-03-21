Development roadmap
===================

Towards v1.0
------------
In rough order of priority:

- Update and add tests for Request.preview_data().
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
- Remove `odo` as a dependency; suggest its use in the documentation.

Future
------

Using pd.DataFrame for internal storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The work in this branch handles Observations as object instances. Once the
implementation is complete and fully conforms to the spec, the package might
be refactored again to use pandas objects for internal storage. See:

- pandasdmx/experimental.py for a partial mock-up of such code, and
- tests/test_experimental.py for tests.

Choosing either the current or experimental DataSet as a default should be
based on detailed performance (memory and time) evaluation under a variety of
use-cases. To that end, note that the experimental DataSet involves three
conversions:

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

SDMX features & miscellaneous
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Check for functionality of pysdmx_ (direct ancestor of pandaSDMX) and
  sdmx.py_ (distinct); ensure pandaSDMX offers a superset of these features.

- Serialize Message objects as SDMX-JSON or SDMX-ML.

- SDMX features:

  - Cube and Constraints.
  - SOAP APIs; currently only REST APIs are supported. This would allow access
    to, e.g., a broader set of :ref:`IMF` data.

- Performance:

  - Optimize or relax use of traitlets. As mentioned above, parsing some
    messages can be slow. Install pytest-profiling_ and run, for instance::

        $ py.test --profile --profile-svg -k INSEE
        $ python3 -m pstats prof/combined.prof
        % sort cumulative
        % stats

    This gives output like the following, with a total time of 7.2 s. Traitlets
    methods are called a large number of times (32199 for the INSEE tests) and
    their execution takes up about half of the loading time.

    .. code::

                 ncalls  tottime  percall  cumtime  percall type     filename:lineno(function)
                      6    0.002    0.000    7.124    1.187          pandasdmx/api.py:457(open_file)
                      6    0.001    0.000    7.104    1.184          pandasdmx/reader/sdmxml.py:255(read_message)
                 7758/6    0.244    0.000    7.076    1.179          pandasdmx/reader/sdmxml.py:342(_parse)
                      1    0.003    0.003    5.046    5.046          tests/test_insee.py:42(test_load_dataset)
                      3    0.000    0.000    4.458    1.486          pandasdmx/reader/sdmxml.py:599(parse_dataset)
                     24    0.002    0.000    4.390    0.183          pandasdmx/reader/sdmxml.py:668(parse_series)
                   3988    0.035    0.000    4.146    0.001          pandasdmx/reader/sdmxml.py:646(parse_obs)
                  32199    0.060    0.000    3.770    0.000 package  traitlets/traitlets.py:950(__new__)
                  32199    0.053    0.000    3.700    0.000 package  traitlets/traitlets.py:982(setup_instance)
                  32199    0.640    0.000    3.647    0.000 package  traitlets/traitlets.py:961(setup_instance)
                      3    0.000    0.000    2.611    0.870          pandasdmx/reader/sdmxml.py:680(parse_structures)
               2907/680    0.073    0.000    2.575    0.004          pandasdmx/reader/sdmxml.py:427(_named)
                 207639    0.362    0.000    1.758    0.000 package  traitlets/traitlets.py:516(instance_init)
                   4012    0.046    0.000    1.690    0.000          pandasdmx/reader/sdmxml.py:553(parse_attributes)
                  21616    0.104    0.000    1.653    0.000 package  traitlets/traitlets.py:988(__init__)
                 135542    0.127    0.000    1.223    0.000 package  traitlets/traitlets.py:1690(instance_init)
                      1    0.000    0.000    1.219    1.219          tests/test_insee.py:87(test_fixe_key_names)
          245653/237457    0.157    0.000    1.218    0.000 package  contextlib.py:85(__exit__)
          491315/474920    0.139    0.000    1.213    0.000 built-in method builtins.next
                    665    0.002    0.000    1.134    0.002          pandasdmx/reader/sdmxml.py:768(parse_dataflow)
                      7    0.000    0.000    1.010    0.144          pandasdmx/reader/sdmxml.py:739(parse_codelist)
                      1    0.000    0.000    0.984    0.984          tests/test_insee.py:119(test_freq_in_series_attribute)
                  43232    0.195    0.000    0.970    0.000 package  traitlets/traitlets.py:1067(hold_trait_notifications)
                   1653    0.006    0.000    0.957    0.001          pandasdmx/reader/sdmxml.py:708(parse_code)
                 100828    0.179    0.000    0.857    0.000 package  traitlets/traitlets.py:558(set)
          496355/484597    0.107    0.000    0.814    0.000 package  traitlets/traitlets.py:545(__get__)
                 224305    0.502    0.000    0.737    0.000 package  traitlets/traitlets.py:486(_dynamic_default_callable)
          168543/162729    0.087    0.000    0.711    0.000 package  traitlets/traitlets.py:526(get)
                  57239    0.030    0.000    0.632    0.000 package  traitlets/traitlets.py:576(__set__)
                   3988    0.027    0.000    0.597    0.000          pandasdmx/reader/sdmxml.py:659(parse_obsdimension)
        2655726/2655715    0.445    0.000    0.522    0.000 built-in method builtins.getattr
                   1472    0.009    0.000    0.520    0.000          pandasdmx/reader/sdmxml.py:405(_maintained)
                   5814    0.009    0.000    0.509    0.000          pandasdmx/model.py:147(make_dynamic_default)
                  32199    0.508    0.000    0.508    0.000 built-in method builtins.dir
          188446/171338    0.143    0.000    0.507    0.000 package  traitlets/traitlets.py:587(_validate)
                    786    0.010    0.000    0.457    0.001          pandasdmx/reader/sdmxml.py:497(parse_ref)
            60028/51832    0.036    0.000    0.446    0.000 built-in method builtins.setattr
                  18451    0.029    0.000    0.400    0.000 package  traitlets/traitlets.py:2264(instance_init)
                  57229    0.241    0.000    0.385    0.000 package  traitlets/traitlets.py:1142(notify_change)
                  19370    0.030    0.000    0.371    0.000 package  traitlets/traitlets.py:2566(instance_init)
                   4202    0.008    0.000    0.367    0.000          pandasdmx/model.py:799(__init__)
                  43589    0.041    0.000    0.352    0.000 package  traitlets/traitlets.py:1336(set_trait)
                 245653    0.100    0.000    0.314    0.000 package  contextlib.py:157(helper)

    If test coverage is sufficient and detailed, then traitlets can be
    converted to simple attributes for the most-used pandasdmx.model classes.
    Alternately, current code that relies on constructing temporary objects can
    be rewritten to avoid this.

Inline TODOs
~~~~~~~~~~~~

.. todolist::

.. _pytest-profiling: https://pypi.org/project/pytest-profiling/
.. _pysdmx: https://github.com/srault95/pysdmx
.. _sdmx.py: https://github.com/mwilliamson/sdmx.py
