from pandasdmx.utils import namedtuple_factory, concat_namedtuples


def test_concat_namedtuples():
    num = list(range(26))
    chars = [chr(65 + i) for i in num]
    limits = [0, 4, 5, 8, 14, 22, 25]
    tuples = []
    for i in range(len(limits) - 1):
        newtype = namedtuple_factory('Test', chars[limits[i]:limits[i + 1]])
        t = newtype(*num[limits[i]:limits[i + 1]])
        tuples.append(t)
    concat1 = concat_namedtuples(*tuples)
    assert isinstance(concat1, tuple)
    assert concat1.A == 0
