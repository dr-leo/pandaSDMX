Ten-line usage example
======================

Suppose we want to analyze annual unemployment data for some European countries.
All we need to know in advance is the data provider: Eurostat.

pandaSDMX makes it easy to search the directory of dataflows, and the complete
structural metadata about the datasets available through the selected dataflow.
We will skip this step here; for details, see :doc:`the walkthrough
<walkthrough>`. The data we want is in the dataflow with the identifier
``une_rt_a``. This dataflow references a data structure with the ID
``DSD_une_rt_a``, that contains or references all the metadata describing data
sets available through this dataflow: the dimensions, concept schemes, and
corresponding code lists.

.. ipython:: python

    import pandasdmx as sdmx
    estat = sdmx.Request('ESTAT')

    # Download the metadata and expose
    metadata = estat.datastructure('DSD_une_rt_a')
    metadata

    # Show some code lists
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

    # Convert to a pandas.Series and select on the 'AGE' dimension
    data = (sdmx.to_pandas(resp)
                .xs('TOTAL', level='AGE', drop_level=False))

    # Explore the data set. First, show dimension names
    data.index.names

    # and corresponding dimension values
    data.index.levels

    # Show aggregate unemployment rates across ages and sexes as
    # percentage of active population
    data.loc[('PC_ACT', 'TOTAL', 'T')]
