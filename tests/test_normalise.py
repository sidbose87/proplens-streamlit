from core.normalise import normalise_jsonld

def test_normalise_basic():
    j = {
        "@type": "House",
        "numberOfBedrooms": 4,
        "numberOfBathroomsTotal": 2,
        "lotSize": {"value": 450, "unitCode": "SQM"},
        "offers": {"price": 1000000}
    }
    out = normalise_jsonld(j)
    assert out["dwelling_type"].value == "House"
    assert out["beds"].value == 4
    assert out["baths"].value == 2
    assert round(out["land_sqm"].value, 2) == 450
    assert out["last_sold_price"].value == 1000000