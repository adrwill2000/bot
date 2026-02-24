"""
chart_generator.py
Fetches OHLCV from Binance (no API key needed) and renders a
styled candlestick chart with volume, EMA20, EMA50, and call entry marker.
Returns a BytesIO PNG buffer.
"""

import io
import logging
from typing import Optional
from datetime import datetime

import requests
import pandas as pd

logger = logging.getLogger(__name__)


def _fetch_ohlcv(symbol: str, interval: str = "4h", limit: int = 100) -> Optional[pd.DataFrame]:
    """Fetch OHLCV candles from Binance public API."""
    pairs_to_try = [
        f"{symbol.upper()}USDT",
        f"{symbol.upper()}USDC",
        f"{symbol.upper()}BTC",
    ]
    base_url = "https://api.binance.com/api/v3/klines"

    for pair in pairs_to_try:
        try:
            resp = requests.get(
                base_url,
                params={"symbol": pair, "interval": interval, "limit": limit},
                timeout=10,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            if not data or isinstance(data, dict):
                continue

            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "qav", "trades", "tbav", "tqav", "ignore"
            ])
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            df = df.set_index("open_time")
            return df

        except Exception as e:
            logger.warning(f"Binance fetch failed for {pair}: {e}")

    return None


def generate_chart(symbol: str, entry_price: Optional[float] = None,
                   target: Optional[float] = None, stop_loss: Optional[float] = None,
                   interval: str = "4h") -> Optional[io.BytesIO]:
    """
    Generate a styled candlestick chart.
    Returns BytesIO PNG or None on failure.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.gridspec import GridSpec
        import matplotlib.dates as mdates
        import warnings
        warnings.filterwarnings("ignore")

        df = _fetch_ohlcv(symbol, interval=interval)
        if df is None or df.empty:
            logger.warning(f"No OHLCV data for {symbol}")
            return None

        # EMAs
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

        # ── Style ────────────────────────────────────────────────────────
        BG       = "#0d1117"
        GRID     = "#1c2333"
        UP_C     = "#00e676"
        DOWN_C   = "#ff1744"
        EMA20_C  = "#ffab40"
        EMA50_C  = "#40c4ff"
        TEXT_C   = "#e6edf3"
        VOL_UP   = "#1b4332"
        VOL_DOWN = "#4a0010"
        ENTRY_C  = "#fff176"
        TARGET_C = "#69f0ae"
        STOP_C   = "#ff5252"

        fig = plt.figure(figsize=(14, 8), facecolor=BG)
        gs = GridSpec(4, 1, figure=fig, hspace=0.04)
        ax  = fig.add_subplot(gs[:3, 0])
        axv = fig.add_subplot(gs[3, 0], sharex=ax)

        ax.set_facecolor(BG)
        axv.set_facecolor(BG)
        for spine in list(ax.spines.values()) + list(axv.spines.values()):
            spine.set_color(GRID)

        ax.tick_params(colors=TEXT_C, labelsize=8)
        axv.tick_params(colors=TEXT_C, labelsize=7)
        ax.yaxis.tick_right()
        axv.yaxis.tick_right()
        plt.setp(ax.get_xticklabels(), visible=False)

        # ── Candles ───────────────────────────────────────────────────────
        width = 0.6 / (24 / {"1h": 1, "4h": 4, "1d": 24, "15m": 0.25}.get(interval, 4))
        for i, (ts, row) in enumerate(df.iterrows()):
            is_up = row["close"] >= row["open"]
            color = UP_C if is_up else DOWN_C
            body_bottom = min(row["open"], row["close"])
            body_height = abs(row["close"] - row["open"])
            # body
            ax.bar(i, body_height, bottom=body_bottom,
                   width=0.6, color=color, linewidth=0, zorder=2)
            # wick
            ax.plot([i, i], [row["low"], row["high"]],
                    color=color, linewidth=0.8, zorder=1)
            # volume
            vol_color = VOL_UP if is_up else VOL_DOWN
            axv.bar(i, row["volume"], width=0.6, color=vol_color, linewidth=0)

        x = list(range(len(df)))
        ax.plot(x, df["ema20"].values, color=EMA20_C, linewidth=1.2, label="EMA 20", zorder=3)
        ax.plot(x, df["ema50"].values, color=EMA50_C, linewidth=1.2, label="EMA 50", zorder=3)

        # ── Entry / Target / Stop markers ─────────────────────────────────
        legend_handles = [
            mpatches.Patch(color=EMA20_C, label="EMA 20"),
            mpatches.Patch(color=EMA50_C, label="EMA 50"),
        ]
        if entry_price:
            ax.axhline(entry_price, color=ENTRY_C, linewidth=1.4, linestyle="--", zorder=4)
            ax.text(len(df)-1, entry_price, f"  Entry ${entry_price:,.4f}",
                    color=ENTRY_C, fontsize=8, va="center", zorder=5)
            legend_handles.append(mpatches.Patch(color=ENTRY_C, label=f"Entry"))
        if target:
            ax.axhline(target, color=TARGET_C, linewidth=1.2, linestyle=":", zorder=4)
            ax.text(len(df)-1, target, f"  Target ${target:,.4f}",
                    color=TARGET_C, fontsize=8, va="center", zorder=5)
            legend_handles.append(mpatches.Patch(color=TARGET_C, label=f"Target"))
        if stop_loss:
            ax.axhline(stop_loss, color=STOP_C, linewidth=1.2, linestyle=":", zorder=4)
            ax.text(len(df)-1, stop_loss, f"  Stop ${stop_loss:,.4f}",
                    color=STOP_C, fontsize=8, va="center", zorder=5)
            legend_handles.append(mpatches.Patch(color=STOP_C, label=f"Stop"))

        ax.grid(True, color=GRID, linewidth=0.5, zorder=0)
        axv.grid(True, color=GRID, linewidth=0.5, axis="y", zorder=0)

        # ── X-axis labels ─────────────────────────────────────────────────
        step = max(1, len(df) // 8)
        axv.set_xticks(range(0, len(df), step))
        date_labels = [df.index[i].strftime("%m/%d %H:%M") for i in range(0, len(df), step)]
        axv.set_xticklabels(date_labels, rotation=30, ha="right", color=TEXT_C, fontsize=7)

        # ── Title and legend ──────────────────────────────────────────────
        current_price = df["close"].iloc[-1]
        pct_24h = ((df["close"].iloc[-1] - df["close"].iloc[-min(6,len(df))]) /
                   df["close"].iloc[-min(6,len(df))]) * 100
        trend_emoji = "📈" if pct_24h >= 0 else "📉"
        color_str = "limegreen" if pct_24h >= 0 else "tomato"

        ax.set_title(
            f"{symbol.upper()}/USDT  •  {interval} Chart  •  ${current_price:,.4f}  "
            f"{trend_emoji} {pct_24h:+.2f}%",
            color=TEXT_C, fontsize=12, fontweight="bold", pad=10
        )

        leg = ax.legend(handles=legend_handles, loc="upper left",
                        facecolor=BG, edgecolor=GRID, labelcolor=TEXT_C, fontsize=8)

        # ── Watermark ─────────────────────────────────────────────────────
        fig.text(0.5, 0.02, "🤡 Call Channel Roast Bot  •  Claude made no mistake",
                 ha="center", color="#30363d", fontsize=8, fontstyle="italic")

        # ── Export ────────────────────────────────────────────────────────
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                    facecolor=BG, edgecolor="none")
        buf.seek(0)
        plt.close(fig)
        return buf

    except Exception as e:
        logger.error(f"Chart generation failed for {symbol}: {e}")
        return None


def get_current_price(symbol: str) -> Optional[float]:
    """Fetch current price from Binance ticker."""
    pairs_to_try = [
        f"{symbol.upper()}USDT",
        f"{symbol.upper()}USDC",
        f"{symbol.upper()}BTC",
    ]
    for pair in pairs_to_try:
        try:
            resp = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": pair},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "price" in data:
                    return float(data["price"])
        except Exception as e:
            logger.warning(f"Price fetch failed for {pair}: {e}")
    return None
