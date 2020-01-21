Ten-line usage example
======================

Suppose we want to analyze annual unemployment data for some European countries.
All we need to know in advance is the data provider: Eurostat.

pandaSDMX makes it easy to search the directory of dataflows, and the complete
structural metadata about the datasets available through the selected dataflow.
(We will skip this step here; see :doc:`the walkthrough
<walkthrough>`.)

The data we want is in the dataflow with the identifier ``une_rt_a``.
This dataflow references a data structure with the ID ``DSD_une_rt_a``, that contains or references all the metadata describing data sets available through this dataflow: the dimensions, concept schemes, and corresponding code lists.

.. ipython:: python

    import pandasdmx as sdmx
    estat = sdmx.Request('ESTAT')

Download the metadata and expose:

.. ipython:: python

    metadata = estat.datastructure('DSD_une_rt_a')
    metadata

Explore the contents of some code lists:

.. ipython:: python

    for cl in 'CL_AGE', 'CL_UNIT':
        print(sdmx.to_pandas(metadata.codelist[cl]))

Next we download a dataset. We use codes from the code list 'GEO'
to obtain data on Greece, Ireland and Spain only.

.. ipython:: python

    resp = estat.data(
        'une_rt_a',
        key={'GEO': 'EL+ES+IE'},
        params={'startPeriod': '2007'},
        )

Convert to a :class:`pandas.Series` and select on the ``AGE`` dimension:

.. ipython:: python

    data = (sdmx.to_pandas(resp)
                .xs('TOTAL', level='AGE', drop_level=False))

We can now explore the data set as expressed in a familiar pandas object.
First, show dimension names:

.. ipython:: python

    data.index.names


…and corresponding key values along these dimensions:

.. ipython:: python

    data.index.levels

Select some data of interest: show aggregate unemployment rates across ages and sexes, as percentage of active population:

.. ipython:: python

    data.loc[('PC_ACT', 'TOTAL', 'T')]
