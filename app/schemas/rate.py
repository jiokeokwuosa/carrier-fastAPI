"""Pydantic schemas for rate quote requests and responses."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    # Shared base: camelCase in JSON, snake_case in Python (see schemas/auth.py).
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_by_alias=True,
    )


class UnitOfMeasurementSchema(CamelModel):
    code: str
    description: str


class DimensionsSchema(CamelModel):
    unit_of_measurement: UnitOfMeasurementSchema
    length: str
    width: str
    height: str


class PackageWeightSchema(CamelModel):
    unit_of_measurement: UnitOfMeasurementSchema
    weight: str


class PackageSchema(CamelModel):
    dimensions: DimensionsSchema
    package_weight: PackageWeightSchema


class AddressSchema(CamelModel):
    address_line: List[str] = Field(min_length=1)
    country_code: str


class RateRequestSchema(CamelModel):
    origin: AddressSchema
    destination: AddressSchema
    package: PackageSchema
    service_level: Optional[str] = None


class MonetaryValueSchema(CamelModel):
    currency_code: str
    monetary_value: str


class ServiceSchema(CamelModel):
    code: str
    description: str


class BillingWeightSchema(CamelModel):
    unit_of_measurement: UnitOfMeasurementSchema
    weight: str


class RateQuoteSchema(CamelModel):
    service: ServiceSchema
    total_charges: MonetaryValueSchema
    total_charges_with_taxes: Optional[MonetaryValueSchema] = None
    transportation_charges: MonetaryValueSchema
    billing_weight: BillingWeightSchema


class RateResponseSchema(CamelModel):
    quotes: List[RateQuoteSchema]
    count: int


class ErrorResponseSchema(BaseModel):
    """Legacy shape — not used by current error handlers (see app.main)."""

    status_code: int
    code: str
    message: str
    details: Optional[dict] = None
