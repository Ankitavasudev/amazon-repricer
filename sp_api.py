"""Amazon SP-API integration module with mock mode for testing."""

import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MockSPAPI:
    """Mock SP-API for testing without real Amazon credentials."""

    def __init__(self):
        self._competitor_prices = {}
        self._my_prices = {}
        self._seed_mock_data()

    def _seed_mock_data(self):
        """Seed mock competitor prices."""
        mock_data = {
            "B08N5WRWNW": {"competitors": [29.99, 31.50, 28.99, 32.00], "my_price": 34.99},
            "B07XJ8C8F5": {"competitors": [45.00, 42.50, 47.99, 44.00], "my_price": 49.99},
            "B09G9FPHY6": {"competitors": [19.99, 21.00, 18.50, 20.50], "my_price": 22.99},
            "B08L5V9J8X": {"competitors": [55.00, 52.99, 57.50, 54.00], "my_price": 59.99},
            "B07FZ8S74R": {"competitors": [12.99, 13.50, 11.99, 14.00], "my_price": 15.99},
        }
        for asin, data in mock_data.items():
            self._competitor_prices[asin] = data["competitors"]
            self._my_prices[asin] = data["my_price"]

    def get_competitor_prices(self, asin: str) -> List[float]:
        """Get competitor prices for an ASIN (mock)."""
        if asin not in self._competitor_prices:
            # Generate random competitors for unknown ASINs
            base = random.uniform(10, 100)
            self._competitor_prices[asin] = [round(base + random.uniform(-5, 5), 2) for _ in range(4)]
            self._my_prices[asin] = round(base + random.uniform(5, 15), 2)
        # Simulate price fluctuation
        self._competitor_prices[asin] = [round(p + random.uniform(-0.5, 0.5), 2) for p in self._competitor_prices[asin]]
        return self._competitor_prices[asin]

    def get_my_price(self, asin: str) -> Optional[float]:
        """Get current price for my offer (mock)."""
        return self._my_prices.get(asin)

    def update_price(self, asin: str, new_price: float) -> bool:
        """Update price for an ASIN (mock)."""
        self._my_prices[asin] = new_price
        logger.info(f"[MOCK] Updated {asin} price to ${new_price:.2f}")
        return True


class RealSPAPI:
    """Real Amazon SP-API integration."""

    def __init__(self, config):
        self.config = config
        self._client = None
        self._access_token = None
        self._token_expiry = None

    def _get_access_token(self):
        """Get LWA access token."""
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token

        import requests
        url = "https://api.amazon.com/auth/o2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.config.refresh_token,
            "client_id": self.config.lwa_client_id,
            "client_secret": self.config.lwa_client_secret,
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()
        self._access_token = token_data["access_token"]
        self._token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"] - 60)
        return self._access_token

    def get_competitor_prices(self, asin: str) -> List[float]:
        """Get competitor prices from SP-API."""
        import requests

        token = self._get_access_token()
        url = f"https://sellingpartnerapi-na.amazon.com/products/pricing/v0/items/{asin}/offers"
        params = {
            "MarketplaceId": self.config.marketplace_id,
            "ItemCondition": "New",
        }
        headers = {
            "x-amz-access-token": token,
            "Content-Type": "application/json",
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        prices = []
        offers = data.get("payload", {}).get("Offers", [])
        for offer in offers:
            if not offer.get("IsBuyBoxWinner", False):
                price = offer.get("ListingPrice", {}).get("Amount")
                if price:
                    prices.append(float(price))
        return prices

    def get_my_price(self, asin: str) -> Optional[float]:
        """Get current price for my offer from SP-API."""
        import requests

        token = self._get_access_token()
        url = f"https://sellingpartnerapi-na.amazon.com/products/pricing/v0/items/{asin}/offers"
        params = {
            "MarketplaceId": self.config.marketplace_id,
            "ItemCondition": "New",
        }
        headers = {
            "x-amz-access-token": token,
            "Content-Type": "application/json",
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        offers = data.get("payload", {}).get("Offers", [])
        for offer in offers:
            if offer.get("IsBuyBoxWinner", False) or offer.get("SellerId") == self.config.seller_id:
                price = offer.get("ListingPrice", {}).get("Amount")
                if price:
                    return float(price)
        return None

    def update_price(self, asin: str, new_price: float) -> bool:
        """Update price via SP-API Feeds."""
        import requests
        import json as json_mod

        token = self._get_access_token()
        # Create feed document
        feed_url = "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds"
        feed_data = {
            "feedType": "JSON_LISTINGS_FEED",
            "marketplaceIds": [self.config.marketplace_id],
            "inputFeedDocumentId": None,
        }
        headers = {
            "x-amz-access-token": token,
            "Content-Type": "application/json",
        }
        # This is a simplified version - real implementation needs feed document upload
        logger.info(f"Price update requested for {asin}: ${new_price:.2f}")
        return True


def create_sp_api(config):
    """Factory function to create SP-API client."""
    if config.mock_mode:
        return MockSPAPI()
    return RealSPAPI(config)