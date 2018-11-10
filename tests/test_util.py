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


# def test_dictliketrait():
#     class Foo:
#         id = None
#
#     class Bar(HasTraits):
#         members = DictLikeTrait(Instance(Foo))
#
#     bar = Bar()
#
#     a1 = bar.members.get('a')
#     a2 = bar.members.get('a')
#
#     assert a1 is a2
