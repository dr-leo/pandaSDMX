Ten-line usage example
======================

Suppose we want to analyze annual unemployment data for some European countries.
All we need to know in advance is the data provider: Eurostat.

pandaSDMX makes it easy to search the directory of dataflows, and the complete structural metadata about the datasets available through the selected dataflow.
(This example skips these steps; see :doc:`the walkthrough <walkthrough>`.)

The data we want is in a *data flow* with the identifier ``une_rt_a``.
This dataflow references a *data structure definition* (DSD) with the ID ``DSD_une_rt_a``.
The DSD, in turn, contains or references all the metadata describing data sets available through this dataflow: the concepts, things measured, dimensions, and lists of codes used to label each dimension.

.. ipython:: python

    import pandasdmx as sdmx
    estat = sdmx.Request('ESTAT')

Download the metadata:

.. ipython:: python

    metadata = estat.datastructure('DSD_une_rt_a')
    metadata

Explore the contents of some code lists:

.. ipython:: python

    for cl in 'CL_AGE', 'CL_UNIT':
        print(sdmx.to_pandas(metadata.codelist[cl]))

Next we download a dataset.
To obtain data on Greece, Ireland and Spain only, we use codes from the code list 'CL_GEO' to specify a *key* for the dimension named ‘GEO’.
We also use a query *parameter*, 'startPeriod', to limit the scope of the data returned:

.. ipython:: python

    resp = estat.data(
        'une_rt_a',
        key={'GEO': 'EL+ES+IE'},
        params={'startPeriod': '2007'},
        )

``resp`` is  a :class:`.DataMessage` object.
We use its :meth:`~pandasdmx.message.Message.to_pandas` method to convert it to a :class:`pandas.DataFrame`, and select on the ``AGE`` dimension we saw   in the ``metadata`` above:

.. ipython:: python

    data = resp.to_pandas(
        datetime={'dim': 'TIME_PERIOD', 'freq': 'FREQ'}).xs('Y15-74', level='AGE', 
            axis=1, drop_level=False)

We can now explore the data set as expressed in a familiar pandas object.
First, show dimension names:

.. ipython:: python

    data.columns.names

…and corresponding key values along these dimensions:

.. ipython:: python

    data.columns.levels

Select some data of interest: show aggregate unemployment rates across ages ('Y15-74' on the ``AGE`` dimension) and sexes ('T' on the ``SEX`` dimension), expressed as a percentage of active population ('PC_ACT' on the ``UNIT`` dimension):

.. ipython:: python

    data.loc[:, ('Y15-74', 'PC_ACT', 'T')]
