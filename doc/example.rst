Ten-line usage example
======================

Suppose we want to analyze annual unemployment data for some European countries.
All we need to know in advance is the data provider: Eurostat.

pandaSDMX makes it easy to search the directory of dataflows, and the complete
structural metadata about the datasets available through the selected dataflow.
We will skip this step here; the impatient reader may directly jump to
:ref:`basic-usage`. The dataflow with the ID "une_rt_a" contains the data we
want; this dataflow references a data structure with the ID "DSD_une_rt_a".

It contains or references all the metadata describing data sets available
through this dataflow: the dimensions, concept schemes, and corresponding code
lists.

.. ipython:: python

    from pandasdmx import Request, to_pandas
    estat = Request('ESTAT')

    # Download the metadata and expose
    metadata = estat.datastructure('DSD_une_rt_a')

    # Show some code lists
    to_pandas(metadata.codelist['CL_AGE'])
    to_pandas(metadata.codelist['CL_UNIT'])

Next we download a dataset. We use codes from the code list 'GEO'
to obtain data on Greece, Ireland and Spain only.

.. ipython:: python

    resp = estat.data('une_rt_a', key={'GEO': 'EL+ES+IE'},
                      params={'startPeriod': '2007'})

    # Convert to a pandas.Series and select on the 'AGE' dimension
    data = to_pandas(resp.data[0]).xs('TOTAL', level='AGE', drop_level=False)

    # Explore the data set. First, show dimension names
    data.index.names

    # and corresponding dimension values
    data.index.levels

    # Show aggregate unemployment rates across ages and sexes as
    # percentage of active population
    data.loc[('PC_ACT', 'TOTAL', 'T')]
