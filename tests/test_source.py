from pandasdmx.source import add_source, list_sources, sources


def test_list_sources():
    source_ids = list_sources()
    assert len(source_ids) == 14

    # Listed alphabetically
    assert source_ids[0] == 'ABS'
    assert source_ids[-1] == 'WB'


def test_source_support():
    # Implicitly supported endpoint
    assert sources['ILO'].supports['categoryscheme']

    # Specifically unsupported endpoint
    assert not sources['ECB'].supports['datastructure']

    # Explicitly supported structure-specific data
    assert sources['INEGI'].supports['structure-specific data']


def test_add_source():
    profile = """{
        "id": "FOO",
        "url": "https://example.org/sdmx"
        }"""
    add_source(profile)
