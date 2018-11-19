from pandasdmx.source import add_source, list_sources


def test_list_sources():
    source_ids = list_sources()
    assert len(source_ids) == 10
    assert source_ids[0] == 'ABS'
    assert source_ids[-1] == 'WBG_WITS'


def test_add_source():
    profile = """{
        "id": "FOO",
        "url": "https://example.org/sdmx"
        }"""
    add_source(profile)
