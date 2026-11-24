"""Configuration module for Amazon Repricer."""

import csv
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ASINConfig:
    asin: str
    min_price: float
    max_price: Optional[float] = None
    enabled: bool = True


@dataclass
class RepricerConfig:
    seller_id: str = ""
    marketplace_id: str = "ATVPDKIKX0DER"  # US marketplace
    region: str = "us-east-1"
    access_key: str = ""
    secret_key: str = ""
    refresh_token: str = ""
    lwa_client_id: str = ""
    lwa_client_secret: str = ""
    mock_mode: bool = True  # Set to False for real SP-API
    schedule_interval_minutes: int = 30
    log_file: str = "repricer.log"
    asins: List[ASINConfig] = field(default_factory=list)

    @classmethod
    def from_env(cls):
        """Load config from environment variables."""
        config = cls(
            seller_id=os.getenv("SELLER_ID", ""),
            marketplace_id=os.getenv("MARKETPLACE_ID", "ATVPDKIKX0DER"),
            region=os.getenv("REGION", "us-east-1"),
            access_key=os.getenv("AWS_ACCESS_KEY_ID", ""),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            refresh_token=os.getenv("SP_API_REFRESH_TOKEN", ""),
            lwa_client_id=os.getenv("LWA_CLIENT_ID", ""),
            lwa_client_secret=os.getenv("LWA_CLIENT_SECRET", ""),
            mock_mode=os.getenv("MOCK_MODE", "true").lower() == "true",
            schedule_interval_minutes=int(os.getenv("SCHEDULE_INTERVAL", "30")),
            log_file=os.getenv("LOG_FILE", "repricer.log"),
        )
        return config

    @classmethod
    def from_json(cls, path: str):
        """Load config from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        config = cls(
            seller_id=data.get("seller_id", ""),
            marketplace_id=data.get("marketplace_id", "ATVPDKIKX0DER"),
            region=data.get("region", "us-east-1"),
            access_key=data.get("access_key", ""),
            secret_key=data.get("secret_key", ""),
            refresh_token=data.get("refresh_token", ""),
            lwa_client_id=data.get("lwa_client_id", ""),
            lwa_client_secret=data.get("lwa_client_secret", ""),
            mock_mode=data.get("mock_mode", True),
            schedule_interval_minutes=data.get("schedule_interval_minutes", 30),
            log_file=data.get("log_file", "repricer.log"),
        )
        # Load ASINs from CSV if specified
        asin_file = data.get("asin_file", "asins.csv")
        if os.path.exists(asin_file):
            config.load_asins_from_csv(asin_file)
        return config

    def load_asins_from_csv(self, path: str):
        """Load ASINs and min prices from CSV file."""
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.asins.append(ASINConfig(
                    asin=row["asin"].strip(),
                    min_price=float(row["min_price"]),
                    max_price=float(row["max_price"]) if row.get("max_price") else None,
                    enabled=row.get("enabled", "true").lower() == "true",
                ))

    def validate(self) -> bool:
        """Validate configuration."""
        if not self.mock_mode:
            required = ["seller_id", "access_key", "secret_key", "refresh_token", "lwa_client_id", "lwa_client_secret"]
            for field_name in required:
                if not getattr(self, field_name):
                    return False
        if not self.asins:
            return False
        return True