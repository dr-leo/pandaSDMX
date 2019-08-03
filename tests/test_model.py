# TODO test str() and repr() implementations

from pandasdmx.model import (
    DEFAULT_LOCALE,
    AttributeValue,
    ConceptScheme,
    ContentConstraint,
    ConstraintRole,
    ConstraintRoleType,
    CubeRegion,
    DataAttribute,
    DataSet,
    DataStructureDefinition,
    DataflowDefinition,
    Dimension,
    Item,
    Key,
    Observation,
    )
import pydantic
from pytest import raises


def test_itemscheme_setdefault():
    # Setting works even if the 'items' trait has not been initialized
    cs = ConceptScheme()
    cs.setdefault(id='FOO')


def test_contentconstraint():
    crole = ConstraintRole(role=ConstraintRoleType['allowable'])
    cr = ContentConstraint(role=crole)
    cr.content = {DataflowDefinition()}
    cr.data_content_region = CubeRegion(included=True, member={})


def test_dataset():
    # Enumeration values can be used to initialize
    from pandasdmx.model import ActionType
    print(ActionType)
    DataSet(action=ActionType['information'])


def test_datastructuredefinition():
    dsd = DataStructureDefinition()

    # Convenience methods
    da = dsd.attribute(id='foo')
    assert isinstance(da, DataAttribute)

    d = dsd.dimension(id='baz', order=-1)
    assert isinstance(d, Dimension)


def test_dimension():
    # Constructor
    Dimension(id='CURRENCY', order=0)


def test_internationalstring():
    # Constructor; the .name attribute is an InternationalString
    i = Item(id='ECB')

    # Set and get using the attribute directly
    i.name.localizations['DE'] = 'Europäische Zentralbank'
    assert i.name.localizations['DE'] == 'Europäische Zentralbank'

    # Set and get using item convenience
    i.name['FR'] = 'Banque centrale européenne'
    assert len(i.name.localizations) == 2
    assert i.name['FR'] == 'Banque centrale européenne'

    # repr() gives all localizations
    assert repr(i.name) == '\n'.join(sorted([
        'DE: Europäische Zentralbank',
        'FR: Banque centrale européenne',
        ]))

    # Setting with a string directly sets the value in the default locale
    i.name = 'European Central Bank'
    assert len(i.name.localizations) == 1
    assert i.name.localizations[DEFAULT_LOCALE] == 'European Central Bank'

    # Setting with a (locale, text) tuple
    i.name = ('FI', 'Euroopan keskuspankki')
    assert len(i.name.localizations) == 1

    # Setting with a dict()
    i.name = {'IT': 'Banca centrale europea'}
    assert len(i.name.localizations) == 1

    # Using some other type is an error
    with raises(pydantic.ValidationError):
        i.name = 123

    # Same, but in the constructor
    i2 = Item(id='ECB', name='European Central Bank')

    # str() uses the default locale
    assert str(i2.name) == 'European Central Bank'


def test_item():
    items = []
    for i in range(10):
        items.append(Item(id='Foo {}'.format(i)))

        if i > 0:
            items[-1].parent = items[-2]
            items[-2].child.append(items[-1])

    assert items[-1] in items[0]


def test_key():
    # Construct with a dict
    k1 = Key({'foo': 1, 'bar': 2})

    # Construct with kwargs
    k2 = Key(foo=1, bar=2)

    # Results are __eq__ each other
    assert k1 == k2

    # Doing both is an error
    with raises(ValueError):
        Key({'foo': 1}, bar=2)

    # __len__
    assert len(k1) == 2

    # __contains__: symmetrical if keys are identical
    assert k1 in k2
    assert k2 in k1
    assert Key(foo=1) in k1
    assert k1 not in Key(foo=1)

    # Set and get using item convenience
    k1['baz'] = 3  # bare value is converted to a KeyValue
    assert k1['foo'] == 1

    # __str__
    assert str(k1) == '(foo=1, bar=2, baz=3)'

    # copying: returns a new object equal to the old one
    k2 = k1.copy()
    assert id(k1) != id(k2) and k1 == k2
    # copy with changes
    k2 = Key(foo=1, bar=2).copy(baz=3)
    assert id(k1) != id(k2) and k1 == k2

    # __add__: Key with something else
    with raises(NotImplementedError):
        k1 + 4
    # Two Keys
    k2 = Key(foo=1) + Key(bar=2)
    assert k2 == k1

    # __radd__: adding a Key to None produces a Key
    assert None + k1 == k1
    # anything else is an error
    with raises(NotImplementedError):
        4 + k1

    # get_values(): preserve ordering
    assert k1.get_values() == (1, 2, 3)


def test_observation():
    obs = Observation()

    # Set by item name
    obs.attached_attribute['TIME_PERIOD'] = 3
    # NB the following does not work; see Observation.attrib()
    # obs.attrib['TIME_PERIOD'] = 3

    obs.attached_attribute['CURRENCY'] = 'USD'

    # Access by attribute name
    assert obs.attrib.TIME_PERIOD == 3
    assert obs.attrib.CURRENCY == 'USD'

    # Access by item index
    assert obs.attrib[1] == 'USD'

    # Add attributes
    obs.attached_attribute['FOO'] = '1'
    obs.attached_attribute['BAR'] = '2'
    assert obs.attrib.FOO == '1' and obs.attrib['BAR'] == '2'

    # Using classes
    da = DataAttribute(id='FOO')
    av = AttributeValue(value_for=da, value='baz')
    obs.attached_attribute[da.id] = av
    assert obs.attrib[da.id] == 'baz'
