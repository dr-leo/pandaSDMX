from pandasdmx.util import DictLike


def test_dictlike():
    dl = DictLike()

    # Set by item name
    dl['TIME_PERIOD'] = 3

    # Set by attribute name
    dl.CURRENCY = 'USD'

    # Access by attribute name
    assert dl.TIME_PERIOD == 3

    # Access by item index
    assert dl[1] == 'USD'
