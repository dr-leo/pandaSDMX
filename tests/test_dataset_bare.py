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
    # TODO populate message data:
    obs = SeriesObservation(None, 1.5931, None)

    # SeriesObservation(
    #     dim=GenericObservationKey(
    #         FREQ='D',
    #         CURRENCY='NZD',
    #         CURRENCY_DENOM='EUR',
    #         EXR_TYPE='SP00',
    #         EXR_SUFFIX='A',
    #         TIME_PERIOD='2013-01-18'),
    #     value=1.5931,
    #     attrib=ObsAttributes(TITLE=None, OBS_STATUS='A')
    #     )
    # SeriesObservation(
    #     dim=GenericObservationKey(
    #         FREQ='D',
    #         CURRENCY='NZD',
    #         CURRENCY_DENOM='EUR',
    #         EXR_TYPE='SP00',
    #         EXR_SUFFIX='A',
    #         TIME_PERIOD='2013-01-21'),
    #     value=1.5925,
    #     attrib=ObsAttributes(TITLE=None, OBS_STATUS='A')
    #     )
    # SeriesObservation(
    #     dim=GenericObservationKey(
    #         FREQ='D',
    #         CURRENCY='RUB',
    #         CURRENCY_DENOM='EUR',
    #         EXR_TYPE='SP00',
    #         EXR_SUFFIX='A',
    #         TIME_PERIOD='2013-01-18'),
    #     value=40.3426,
    #     attrib=ObsAttributes(TITLE=None, OBS_STATUS='A')
    #     )
    # SeriesObservation(
    #     dim=GenericObservationKey(
    #         FREQ='D',
    #         CURRENCY='RUB',
    #         CURRENCY_DENOM='EUR',
    #         EXR_TYPE='SP00',
    #         EXR_SUFFIX='A',
    #         TIME_PERIOD='2013-01-21'),
    #     value=40.3,
    #     attrib=ObsAttributes(TITLE=None, OBS_STATUS='A'))
    msg.data = ds

    # Write to pd.Dataframe
    Writer(msg).write(msg)  # FIXME fails; no msg.data
