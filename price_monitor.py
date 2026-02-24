"""
price_monitor.py
Background price monitoring. Every N minutes, checks all open calls.
If any coin has moved 50%+ from call entry, fires a spike alert.
"""

import logging
import asyncio
from typing import Callable, Awaitable

from chart_generator import get_current_price

logger = logging.getLogger(__name__)


class PriceMonitor:
    def __init__(self, db, app, spike_callback: Callable, spike_threshold: float = 50.0):
        self.db = db
        self.app = app
        self.spike_callback = spike_callback
        self.spike_threshold = spike_threshold

    async def check_prices(self, context=None):
        """
        Called by APScheduler / JobQueue every N minutes.
        Checks all open, non-alerted calls for 50%+ moves.
        """
        calls = self.db.get_open_calls_for_monitoring()
        if not calls:
            return

        logger.info(f"[PriceMonitor] Checking {len(calls)} open calls...")

        for call in calls:
            coin = call["coin"]
            entry = call["entry_price"]

            try:
                current = await asyncio.get_event_loop().run_in_executor(
                    None, get_current_price, coin
                )
                if current is None:
                    continue

                pnl_pct = ((current - entry) / entry) * 100

                if abs(pnl_pct) >= self.spike_threshold:
                    logger.info(
                        f"[PriceMonitor] SPIKE: {coin} moved {pnl_pct:+.1f}% "
                        f"from ${entry} → ${current} (call #{call['id']})"
                    )
                    self.db.mark_spike_alerted(call["id"])
                    await self.spike_callback(
                        app=self.app,
                        coin=coin,
                        entry_price=entry,
                        current_price=current,
                        pnl_pct=pnl_pct,
                        caller_user_id=call["user_id"],
                        call_id=call["id"],
                        chat_id=call.get("chat_id", 0),
                    )

            except Exception as e:
                logger.error(f"[PriceMonitor] Error checking {coin}: {e}")
