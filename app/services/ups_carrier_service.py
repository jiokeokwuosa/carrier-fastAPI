"""UPS Rating API client — builds requests, calls UPS, normalizes quotes."""

import logging
from typing import List, Optional
from urllib.parse import urlencode

import httpx

from app.carriers import Carrier
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    CarrierError,
    NetworkError,
    RateRequestError,
    TimeoutError,
)
from app.schemas.rate import (
    BillingWeightSchema,
    MonetaryValueSchema,
    RateQuoteSchema,
    RateRequestSchema,
    ServiceSchema,
    UnitOfMeasurementSchema,
)
from app.services.carrier_auth_service import CarrierAuthService

logger = logging.getLogger(__name__)


class UpsCarrierService(Carrier):
    PLATFORM = "UPS"

    def __init__(self, carrier_auth_service: CarrierAuthService):
        self.carrier_auth_service = carrier_auth_service

    def get_platform(self) -> str:
        return self.PLATFORM

    def get_rates(self, request: RateRequestSchema) -> List[RateQuoteSchema]:
        try:
            access_token = self.carrier_auth_service.return_access_token(self.PLATFORM)
            ups_request = self._build_ups_request(request)
            response = self._make_rate_request(ups_request, access_token)
            return self._normalize_response(response)
        except CarrierError:
            raise  # Already mapped; let the global handler format the response
        except Exception as exc:
            raise RateRequestError(f"Failed to get rates: {exc}", {"error": str(exc)}) from exc

    def _build_ups_request(self, request: RateRequestSchema) -> dict:
        # Map our camelCase API schema to UPS's PascalCase JSON structure.
        return {
            "RateRequest": {
                "Request": {
                    "TransactionReference": {"CustomerContext": "CustomerContext"},
                },
                "Shipment": {
                    "Shipper": {
                        "Address": {
                            "AddressLine": request.origin.address_line,
                            "CountryCode": request.origin.country_code,
                        }
                    },
                    "ShipTo": {
                        "Address": {
                            "AddressLine": request.destination.address_line,
                            "CountryCode": request.destination.country_code,
                        }
                    },
                    "Package": {
                        "Dimensions": {
                            "UnitOfMeasurement": {
                                "Code": request.package.dimensions.unit_of_measurement.code,
                                "Description": request.package.dimensions.unit_of_measurement.description,
                            },
                            "Length": request.package.dimensions.length,
                            "Width": request.package.dimensions.width,
                            "Height": request.package.dimensions.height,
                        },
                        "PackageWeight": {
                            "UnitOfMeasurement": {
                                "Code": request.package.package_weight.unit_of_measurement.code,
                                "Description": request.package.package_weight.unit_of_measurement.description,
                            },
                            "Weight": request.package.package_weight.weight,
                        },
                    },
                },
            }
        }

    def _make_rate_request(self, ups_request: dict, access_token: str) -> dict:
        query = urlencode({"additionalinfo": "string"})
        url = (
            f"{settings.UPS_API_BASE_URL}/api/rating/"
            f"{settings.UPS_RATING_API_VERSION}/Rate?{query}"
        )

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "transId": "string",
                        "transactionSrc": settings.UPS_TRANSACTION_SRC,
                        "Authorization": f"Bearer {access_token}",
                    },
                    json=ups_request,
                )
        except httpx.TimeoutException as exc:
            raise TimeoutError("Rate request timeout") from exc
        except httpx.RequestError as exc:
            raise NetworkError(
                f"Network error during rate request: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise RateRequestError(
                f"UPS API error: {response.status_code} {response.reason_phrase}",
                {"response": response.text},
            )

        data = response.json()
        # UPS signals application-level success with ResponseStatus.Code == "1".
        status_code = (
            data.get("RateResponse", {})
            .get("Response", {})
            .get("ResponseStatus", {})
            .get("Code")
        )
        if status_code != "1":
            description = (
                data.get("RateResponse", {})
                .get("Response", {})
                .get("ResponseStatus", {})
                .get("Description", "Unknown error")
            )
            raise RateRequestError(f"UPS API returned error: {description}", data)

        return data

    def _normalize_response(self, response: dict) -> List[RateQuoteSchema]:
        # UPS may return a single RatedShipment object or a list of them.
        rated_shipments = response.get("RateResponse", {}).get("RatedShipment") or []
        if not rated_shipments:
            return []

        quotes: List[RateQuoteSchema] = []
        for shipment in rated_shipments:
            total_charges_with_taxes: Optional[MonetaryValueSchema] = None
            if shipment.get("TotalChargesWithTaxes"):
                total_charges_with_taxes = MonetaryValueSchema(
                    currency_code=shipment["TotalChargesWithTaxes"]["CurrencyCode"],
                    monetary_value=shipment["TotalChargesWithTaxes"]["MonetaryValue"],
                )

            quotes.append(
                RateQuoteSchema(
                    service=ServiceSchema(
                        code=shipment["Service"]["Code"],
                        description=shipment["Service"]["Description"],
                    ),
                    total_charges=MonetaryValueSchema(
                        currency_code=shipment["TotalCharges"]["CurrencyCode"],
                        monetary_value=shipment["TotalCharges"]["MonetaryValue"],
                    ),
                    total_charges_with_taxes=total_charges_with_taxes,
                    transportation_charges=MonetaryValueSchema(
                        currency_code=shipment["TransportationCharges"]["CurrencyCode"],
                        monetary_value=shipment["TransportationCharges"]["MonetaryValue"],
                    ),
                    billing_weight=BillingWeightSchema(
                        unit_of_measurement=UnitOfMeasurementSchema(
                            code=shipment["BillingWeight"]["UnitOfMeasurement"]["Code"],
                            description=shipment["BillingWeight"]["UnitOfMeasurement"][
                                "Description"
                            ],
                        ),
                        weight=shipment["BillingWeight"]["Weight"],
                    ),
                )
            )
        return quotes
