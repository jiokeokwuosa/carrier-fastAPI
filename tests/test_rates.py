from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import MOCK_UPS_RATE_RESPONSE, VALID_RATE_REQUEST


def _mock_httpx_client(post_impl):
    mock_instance = MagicMock()
    mock_instance.post = AsyncMock(side_effect=post_impl)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_cm


@patch("httpx.AsyncClient")
async def test_get_ups_rates_success(mock_client_cls, client, auth_headers):
    async def post_side_effect(url, **kwargs):
        response = MagicMock()
        response.text = ""
        response.reason_phrase = "OK"
        response.status_code = 200
        if "oauth" in str(url) or "security" in str(url):
            response.json.return_value = {
                "status": "approved",
                "token_type": "Bearer",
                "issued_at": "1700000000000",
                "client_id": "client",
                "access_token": "ups-token",
                "expires_in": "14399",
            }
        else:
            response.json.return_value = MOCK_UPS_RATE_RESPONSE
        return response

    mock_client_cls.return_value = _mock_httpx_client(post_side_effect)

    response = await client.post("/rates/UPS", json=VALID_RATE_REQUEST, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["count"] == 1
    assert data["quotes"][0]["service"]["code"] == "03"
    assert data["quotes"][0]["totalCharges"]["monetaryValue"] == "12.00"


async def test_get_ups_rates_requires_auth(client):
    response = await client.post("/rates/UPS", json=VALID_RATE_REQUEST)
    assert response.status_code == 401


async def test_get_ups_rates_validation_error(client, auth_headers):
    response = await client.post(
        "/rates/UPS",
        json={"origin": {"addressLine": [], "countryCode": ""}},
        headers=auth_headers,
    )
    assert response.status_code == 422
