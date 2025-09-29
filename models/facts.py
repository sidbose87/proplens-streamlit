from pydantic import BaseModel
from typing import Optional, Literal


class AddressResolved(BaseModel):
    query: str
    display_name: str
    lat: float
    lon: float
    suburb: Optional[str]
    state: Optional[str]
    postcode: Optional[str]
    lga: Optional[str]


class FieldValue(BaseModel):
    value: Optional[float | str]
    source: Literal["jsonld","open_data","estimated","user"]
    confidence: float


class PropertyFacts(BaseModel):
    address: AddressResolved
    dwelling_type: FieldValue
    beds: FieldValue
    baths: FieldValue
    cars: FieldValue
    land_sqm: FieldValue
    build_sqm: FieldValue
    last_sold_price: Optional[FieldValue]
    source_urls: list[str]