# backend/amadeus.py
import os
import time
import requests


AMADEUS_TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_FLIGHT_OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"


class AmadeusClient:
    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "").strip()
        self._access_token = None
        self._token_expires_at = 0

        if not self.client_id or not self.client_secret:
            raise ValueError("Missing AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET in environment (.env)")

    def _get_token(self) -> str:
        # token caching
        now = int(time.time())
        if self._access_token and now < (self._token_expires_at - 30):
            return self._access_token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(AMADEUS_TOKEN_URL, data=data, headers=headers, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        self._access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 0))
        self._token_expires_at = now + expires_in
        return self._access_token

    def search_flights(
        self,
        origin_iata: str,
        destination_iata: str,
        departure_date: str,
        adults: int = 1,
        return_date: str | None = None,
        non_stop: bool = False,
        max_results: int = 20,
        currency_code: str = "SAR",
    ) -> dict:
        token = self._get_token()

        params = {
            "originLocationCode": origin_iata.upper(),
            "destinationLocationCode": destination_iata.upper(),
            "departureDate": departure_date,  # YYYY-MM-DD
            "adults": max(1, int(adults)),
            "nonStop": str(bool(non_stop)).lower(),
            "max": max(1, min(int(max_results), 50)),
            "currencyCode": currency_code,
        }
        if return_date:
            params["returnDate"] = return_date  # YYYY-MM-DD

        headers = {"Authorization": f"Bearer {token}"}

        resp = requests.get(AMADEUS_FLIGHT_OFFERS_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
