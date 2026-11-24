"""Repricer logic — matches lowest competitor price, respects floor price."""

import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PriceChange:
    asin: str
    old_price: float
    new_price: float
    competitor_lowest: float
    min_price: float
    reason: str
    timestamp: str


class Repricer:
    def __init__(self, config, sp_api):
        self.config = config
        self.sp_api = sp_api
        self.changes: List[PriceChange] = []

    def reprice_asin(self, asin_config) -> Optional[PriceChange]:
        """Reprice a single ASIN."""
        asin = asin_config.asin
        if not asin_config.enabled:
            logger.info(f"Skipping {asin} (disabled)")
            return None

        # Get competitor prices
        competitor_prices = self.sp_api.get_competitor_prices(asin)
        if not competitor_prices:
            logger.warning(f"No competitor prices found for {asin}")
            return None

        competitor_lowest = min(competitor_prices)
        my_price = self.sp_api.get_my_price(asin)

        if my_price is None:
            logger.warning(f"Could not get current price for {asin}")
            return None

        logger.info(f"{asin}: My price=${my_price:.2f}, Lowest competitor=${competitor_lowest:.2f}, Floor=${asin_config.min_price:.2f}")

        # Decision logic
        if my_price <= competitor_lowest:
            logger.info(f"  -> Already at or below lowest competitor. No change.")
            return None

        # We're higher than lowest competitor — match them
        target_price = competitor_lowest

        # Respect floor price
        if target_price < asin_config.min_price:
            target_price = asin_config.min_price
            logger.info(f"  -> Target below floor. Using floor price ${target_price:.2f}")

        # Respect max price if set
        if asin_config.max_price and target_price > asin_config.max_price:
            target_price = asin_config.max_price
            logger.info(f"  -> Target above max. Using max price ${target_price:.2f}")

        # Don't update if price hasn't changed meaningfully
        if abs(target_price - my_price) < 0.01:
            logger.info(f"  -> Price change too small. No update.")
            return None

        # Update price
        success = self.sp_api.update_price(asin, target_price)
        if not success:
            logger.error(f"  -> Failed to update price for {asin}")
            return None

        change = PriceChange(
            asin=asin,
            old_price=my_price,
            new_price=target_price,
            competitor_lowest=competitor_lowest,
            min_price=asin_config.min_price,
            reason=f"Matched lowest competitor (${competitor_lowest:.2f})",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.changes.append(change)
        logger.info(f"  -> Updated: ${my_price:.2f} -> ${target_price:.2f}")
        return change

    def reprice_all(self) -> List[PriceChange]:
        """Reprice all configured ASINs."""
        self.changes = []
        logger.info(f"Starting reprice cycle for {len(self.config.asins)} ASINs")
        logger.info(f"Mock mode: {self.config.mock_mode}")

        for asin_config in self.config.asins:
            try:
                self.reprice_asin(asin_config)
            except Exception as e:
                logger.error(f"Error repricing {asin_config.asin}: {e}")

        logger.info(f"Reprice cycle complete. {len(self.changes)} price changes made.")
        return self.changes

    def get_summary(self) -> str:
        """Get a summary of the last reprice cycle."""
        if not self.changes:
            return "No price changes made."
        lines = [f"Price changes ({len(self.changes)}):"]
        for c in self.changes:
            lines.append(f"  {c.asin}: ${c.old_price:.2f} -> ${c.new_price:.2f} (competitor lowest: ${c.competitor_lowest:.2f})")
        return "\n".join(lines)