from providers.jsonld_extractor import _is_property_schema

def test_is_property_schema():
    assert _is_property_schema({"@type": "House"})
    assert _is_property_schema({"@type": ["Thing", "Apartment"]})
    assert not _is_property_schema({"@type": "Person"})