#!/usr/bin/env python3
"""
Amazon Repricer — matches lowest competitor price, respects floor price.

Automatically adjusts your Amazon listing prices to match the lowest
competitor offer, never going below your configured minimum (floor) price.
Runs on a schedule, logs every change for full transparency.

Usage:
    python main.py --once --mock          # Test with mock data
    python main.py --once                 # Run once with real SP-API
    python main.py                        # Run on schedule (default 30 min)
    python main.py --interval 15          # Run every 15 minutes
    python main.py --config my.json       # Use custom config file
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

from config import RepricerConfig
from sp_api import create_sp_api
from repricer import Repricer

# ─── Logging Setup ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_once(config):
    """Execute a single reprice cycle and return list of changes."""
    sp_api = create_sp_api(config)
    repricer = Repricer(config, sp_api)
    changes = repricer.reprice_all()

    # Print summary to console
    print("\n" + "=" * 60)
    print("REPRICE SUMMARY")
    print("=" * 60)
    print(repricer.get_summary())
    print("=" * 60)

    # Append to log file for audit trail
    with open(config.log_file, "a") as f:
        f.write(f"\n--- Reprice cycle: {datetime.now().isoformat()} ---\n")
        f.write(repricer.get_summary() + "\n")
        for c in changes:
            f.write(
                f"  {c.asin}: ${c.old_price:.2f} -> ${c.new_price:.2f} | "
                f"competitor: ${c.competitor_lowest:.2f} | floor: ${c.min_price:.2f} | "
                f"{c.reason}\n"
            )

    return changes


def run_scheduled(config):
    """Run reprice on a recurring schedule."""
    interval = config.schedule_interval_minutes * 60
    logger.info(f"Starting scheduled reprice (every {config.schedule_interval_minutes} minutes)")
    logger.info(f"Mock mode: {config.mock_mode}")
    logger.info(f"ASINs configured: {len(config.asins)}")

    while True:
        try:
            run_once(config)
        except Exception as e:
            logger.error(f"Reprice cycle failed: {e}")
        logger.info(f"Next run in {config.schedule_interval_minutes} minutes...")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Repricer - matches lowest competitor price, respects floor price"
    )
    parser.add_argument("--config", "-c", default="config.json",
                        help="Path to config JSON file (default: config.json)")
    parser.add_argument("--asins", default="asins.csv",
                        help="Path to ASINs CSV file (default: asins.csv)")
    parser.add_argument("--once", action="store_true",
                        help="Run once and exit (for cron/Lambda)")
    parser.add_argument("--mock", action="store_true",
                        help="Force mock mode (no Amazon credentials needed)")
    parser.add_argument("--interval", type=int,
                        help="Override schedule interval in minutes")
    args = parser.parse_args()

    # Load configuration
    if os.path.exists(args.config):
        config = RepricerConfig.from_json(args.config)
    else:
        config = RepricerConfig.from_env()

    # Override ASINs file if specified
    if os.path.exists(args.asins):
        config.asins = []
        config.load_asins_from_csv(args.asins)

    # Override mock mode if flag set
    if args.mock:
        config.mock_mode = True

    # Override interval if specified
    if args.interval:
        config.schedule_interval_minutes = args.interval

    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration. Check config.json and asins.csv")
        sys.exit(1)

    logger.info(f"Loaded {len(config.asins)} ASINs")
    logger.info(f"Mock mode: {config.mock_mode}")

    if args.once:
        run_once(config)
    else:
        run_scheduled(config)


if __name__ == "__main__":
    main()