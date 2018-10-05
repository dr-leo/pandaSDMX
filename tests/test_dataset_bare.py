from unittest import TestCase


class TestAPI(TestCase):
    def test_base_reader_abstract(self):
        """BaseReader cannot be instantiated."""
        from pandasdmx.reader import BaseReader
        with self.assertRaises(TypeError):
            BaseReader(None)

    def test_null_reader(self):
        """Instantiate the null reader."""
        from pandasdmx.reader.null import Reader
        Reader()


def test_dataset_bare():
    from collections import namedtuple

    from pandasdmx.model import DataSet, Message, SeriesObservation
    from pandasdmx.writer.data2pandas import Writer

    # Create a bare Message
    msg = Message()

    # Recreate the content from exr-flat.json
    msg.header.dim_at_obs = 'AllDimensions'
    msg.header.id = '62b5f19d-f1c9-495d-8446-a3661ed24753'
    msg.header.prepared = '2012-11-29T08:40:26Z'
    msg.header.sender = 'ECB'

    ds = DataSet()

    # FIXME in exr-flat.json, these are stored in two places:
    #   $.structure.dimensions.dataSet:
    #      FREQ, CURRENCY_DENOM, EXR_TYPE, EXR_SUFFIX
    #   $.structure.dimensions.observation:
    #      CURRENCY, TIME_PERIOD
    #
    # It should be possible to create them programmatically by setting:
    #   msg.structure.dimensions.dataset[0] = Dimension('FREQ'…)
    #   msg.structure.dimensions.observation = …
    GenericObservationKey = namedtuple(
        'GenericObservationKey',
        'FREQ CURRENCY CURRENCY_DENOM EXR_TYPE EXR_SUFFIX TIME_PERIOD',
        )
    key = GenericObservationKey('D', 'NZD', 'EUR', 'SP00', 'A', '2013-01-18')

    # FIXME in exr-flat.json, these are stored at the path:
    #   $.structure.attributes.observation.
    #
    # It should be possible to create them programmatically by setting:
    #   msg.structure.attributes.observation = …
    ObsAttributes = namedtuple('ObsAttributes', 'TITLE OBS_STATUS')
    attrib = ObsAttributes(None, 'A')

    ds.obs.append(SeriesObservation(key, 1.5931, attrib))

    key = key._replace(TIME_PERIOD='2013-01-21')
    ds.obs.append(SeriesObservation(key, 1.5925, attrib))

    key = key._replace(CURRENCY='RUB', TIME_PERIOD='2013-01-18')
    ds.obs.append(SeriesObservation(key, 40.3426, attrib))

    key = key._replace(TIME_PERIOD='2013-01-21')
    ds.obs.append(SeriesObservation(key, 40.3000, attrib))

    msg.data = ds

    # Write to pd.Dataframe
    df = Writer(msg).write(msg)
    print(df)
    assert False  # Works, but still other changes to be made
