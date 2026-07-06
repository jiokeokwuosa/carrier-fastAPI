from unittest.mock import MagicMock, patch

from tests.conftest import MOCK_UPS_RATE_RESPONSE, VALID_RATE_REQUEST


@patch("app.services.ups_carrier_service.httpx.Client")
def test_get_ups_rates_success(mock_client_cls, client, auth_headers):
    mock_token = MagicMock()
    mock_token.status_code = 200
    mock_token.json.return_value = {
        "status": "approved",
        "token_type": "Bearer",
        "issued_at": "1700000000000",
        "client_id": "client",
        "access_token": "ups-token",
        "expires_in": "14399",
    }
    mock_token.text = ""

    mock_rate = MagicMock()
    mock_rate.status_code = 200
    mock_rate.json.return_value = MOCK_UPS_RATE_RESPONSE
    mock_rate.text = ""
    mock_rate.reason_phrase = "OK"

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = [mock_token, mock_rate]
    mock_client_cls.return_value = mock_client

    response = client.post("/rates/UPS", json=VALID_RATE_REQUEST, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["count"] == 1
    assert data["quotes"][0]["service"]["code"] == "03"
    assert data["quotes"][0]["totalCharges"]["monetaryValue"] == "12.00"


def test_get_ups_rates_requires_auth(client):
    response = client.post("/rates/UPS", json=VALID_RATE_REQUEST)
    assert response.status_code == 401


def test_get_ups_rates_validation_error(client, auth_headers):
    response = client.post(
        "/rates/UPS",
        json={"origin": {"addressLine": [], "countryCode": ""}},
        headers=auth_headers,
    )
    assert response.status_code == 422
