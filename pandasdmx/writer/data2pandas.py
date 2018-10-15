

# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in
# this distribution.
# (c) 2014, 2015 Dr. Leo <fhaxbox66qgmail.com>


'''
This module contains a writer class that writes a generic data message to
pandas dataframes or series.
'''
import numpy as np
import pandas as pd

from pandasdmx.model import DataMessage
from pandasdmx.writer import BaseWriter


class Writer(BaseWriter):

    def write(self, source=None, asframe=True, dtype=np.float64,
              attributes='', fromfreq=False, parse_time=True):
        """Transform a :class:`pandasdmx.model.DataMessage` instance to a
        pandas DataFrame or iterator over pandas Series.

        Args:
            source(pandasdmx.model.DataMessage): a pandasdmx.model.DataSet or
                iterator of pandasdmx.model.Series

            asframe(bool): if True, merge the series of values and/or
                attributes into one or two multi-indexed pandas.DataFrame(s),
                otherwise return an iterator of pandas.Series. (default: True)

            dtype(str, np.dtype, None): datatype for values. Defaults to
                np.float64. If None, do not return the values of a series. In
                this case, attributes must not be an empty string so that some
                attribute is returned.

            attributes(str, None): string determining which attributes, if any,
                should be returned in separate series or a separate DataFrame.
                Allowed values: '', 'o', 's', 'g', 'd' or any combination
                thereof such as 'os', 'go'. Defaults to 'osgd'. Where 'o', 's',
                'g', and 'd' mean that attributes at observation, series, group
                and dataset level will be returned as members of
                per-observation namedtuples.
            fromfreq(bool): if True, extrapolate time periods from the first
                item and FREQ dimension. Default: False
            parse_time(bool): if True (default), try to generate datetime
                index, provided that dim_at_obs is 'TIME' or 'TIME_PERIOD'.
                Otherwise, ``parse_time`` is ignored. If False, always generate
                index of strings. Set it to False to increase performance and
                avoid parsing errors for exotic date-time formats unsupported
                by pandas.
        """
        if isinstance(source, DataMessage):
            if len(source.data) == 1:
                return self.write(source.data[0], attributes=attributes)
            else:
                return [self.write(ds, attributes=attributes) for ds in
                        source.data]

        # source will now be a DataSet

        # validate 'attributes'
        if attributes is None or not attributes:
            attributes = ''
        else:
            try:
                attributes = attributes.lower()
            except AttributeError:
                raise TypeError("'attributes' argument must be of type str.")
            if set(attributes) - {'o', 's', 'g', 'd'}:
                raise ValueError(
                    "'attributes' must only contain 'o', 's', 'd' or 'g'.")

        # Convert observations
        result = {}
        for observation in source.obs:
            row = {}
            if dtype:
                row['value'] = observation.value
            if attributes:
                row.update(observation.attrib)
            result[observation.key.order().get_values()] = row

        result = pd.DataFrame.from_dict(result, orient='index')

        if len(result):
            result.index.names = observation.key.order().values.keys()
            if dtype and not attributes:
                result = result['value']

        return result
