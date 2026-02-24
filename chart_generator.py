"""
chart_generator.py
Solana-first price and chart data pipeline.

Resolution priority per task:
  Current price   → Jupiter Price API v2  (primary)
                  → Binance               (fallback for non-Solana majors)

  Token metadata  → Jupiter Token API     (primary)
                  → DexScreener search    (fallback)

  OHLCV candles   → DexScreener           (primary — Jupiter has no candle endpoint)
                  → Binance               (fallback for majors e.g. BTC/ETH)

Input auto-detection:
  - Looks like a Solana CA (base58, 32-44 chars, no lowercase l/0/O/I)  → Solana path
  - Otherwise                                                            → symbol path
    Symbol path tries Jupiter token list first, then Binance
"""

import io
import logging
import re
import time
from typing import Optional, Dict, List, Tuple

import requests

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# HTTP SESSION  (shared, with default timeouts)
# ─────────────────────────────────────────────────────────────────────────────
_session = requests.Session()
_session.headers.update({"User-Agent": "CallChannelRoastBot/3.0"})

def _get(url: str, params: dict = None, timeout: int = 8) -> Optional[dict]:
    try:
        r = _session.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.debug(f"GET {url} failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# INPUT DETECTION
# ─────────────────────────────────────────────────────────────────────────────

# Solana base58 alphabet (no 0, O, I, l)
_B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

def is_solana_ca(value: str) -> bool:
    """True if the string looks like a Solana contract address."""
    return bool(_B58.match(value.strip()))


# ─────────────────────────────────────────────────────────────────────────────
# JUPITER — Price API v2
# ─────────────────────────────────────────────────────────────────────────────

JUPITER_PRICE_URL = "https://api.jup.ag/price/v2"

def jupiter_get_price(mint: str) -> Optional[float]:
    """
    Fetch current USD price for a Solana token via Jupiter Price API v2.
    Returns float or None.
    """
    data = _get(JUPITER_PRICE_URL, params={"ids": mint, "showExtraInfo": "false"})
    if not data:
        return None
    try:
        token_data = data.get("data", {}).get(mint, {})
        price_str  = token_data.get("price")
        if price_str is not None:
            return float(price_str)
    except Exception as e:
        logger.debug(f"Jupiter price parse error for {mint}: {e}")
    return None


def jupiter_get_prices_batch(mints: List[str]) -> Dict[str, float]:
    """
    Fetch prices for multiple mints in one call.
    Returns {mint: price} for those that resolved.
    """
    if not mints:
        return {}
    ids = ",".join(mints)
    data = _get(JUPITER_PRICE_URL, params={"ids": ids, "showExtraInfo": "false"})
    if not data:
        return {}
    result = {}
    for mint, token_data in data.get("data", {}).items():
        try:
            p = token_data.get("price")
            if p is not None:
                result[mint] = float(p)
        except Exception:
            pass
    return result


# ─────────────────────────────────────────────────────────────────────────────
# JUPITER — Token API
# ─────────────────────────────────────────────────────────────────────────────

JUPITER_TOKEN_URL  = "https://tokens.jup.ag/token"
JUPITER_TOKENS_URL = "https://tokens.jup.ag/tokens"

def jupiter_get_token_by_mint(mint: str) -> Optional[Dict]:
    """Fetch token metadata by mint address from Jupiter Token API."""
    return _get(f"{JUPITER_TOKEN_URL}/{mint}")


def jupiter_search_by_symbol(symbol: str) -> Optional[Dict]:
    """
    Search Jupiter's token list for a symbol.
    Returns the first strict match (case-insensitive) or None.
    Uses the ?tags=verified filter to reduce noise.
    """
    # Try verified tokens first
    for tags in ["verified", "community", None]:
        params = {"tags": tags} if tags else {}
        data = _get(JUPITER_TOKENS_URL, params=params, timeout=12)
        if not data or not isinstance(data, list):
            continue
        sym_upper = symbol.upper()
        # Strict match
        for token in data:
            if token.get("symbol", "").upper() == sym_upper:
                return token
        # Partial match fallback (only if strict fails)
        for token in data:
            if sym_upper in token.get("symbol", "").upper():
                return token
    return None


# ─────────────────────────────────────────────────────────────────────────────
# DEXSCREENER — Pair + OHLCV
# ─────────────────────────────────────────────────────────────────────────────

DEXSCREENER_TOKENS_URL  = "https://api.dexscreener.com/latest/dex/tokens"
DEXSCREENER_SEARCH_URL  = "https://api.dexscreener.com/latest/dex/search"
DEXSCREENER_CANDLES_URL = "https://api.dexscreener.com/latest/dex/candles"

def dexscreener_get_pair(mint: str) -> Optional[Dict]:
    """
    Get the best trading pair for a Solana token from DexScreener.
    'Best' = highest liquidity USD pair on Raydium/Orca/Meteora/Pump.
    """
    data = _get(f"{DEXSCREENER_TOKENS_URL}/{mint}")
    if not data:
        return None
    pairs = data.get("pairs") or []
    # Filter to Solana pairs with USD quote
    sol_pairs = [
        p for p in pairs
        if p.get("chainId") == "solana"
        and p.get("quoteToken", {}).get("symbol", "").upper() in ("USDC", "USDT", "SOL")
    ]
    if not sol_pairs:
        sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
    if not sol_pairs:
        sol_pairs = pairs
    if not sol_pairs:
        return None
    # Sort by liquidity USD descending
    sol_pairs.sort(key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
    return sol_pairs[0]


def dexscreener_search_symbol(symbol: str) -> Optional[Dict]:
    """Search DexScreener by symbol, return best Solana pair."""
    data = _get(DEXSCREENER_SEARCH_URL, params={"q": symbol})
    if not data:
        return None
    pairs = data.get("pairs") or []
    sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
    if not sol_pairs:
        sol_pairs = pairs
    if not sol_pairs:
        return None
    sol_pairs.sort(key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
    return sol_pairs[0]


# DexScreener resolution map  interval_str → resolution param
_DS_RESOLUTION = {
    "1m":  "1",
    "5m":  "5",
    "15m": "15",
    "1h":  "60",
    "4h":  "240",
    "1d":  "1440",
}

def dexscreener_get_ohlcv(chain_id: str, pair_address: str,
                           interval: str = "4h", limit: int = 100) -> Optional[List[Dict]]:
    """
    Fetch OHLCV candles from DexScreener.
    Returns list of {time, open, high, low, close, volume} or None.
    """
    resolution = _DS_RESOLUTION.get(interval, "240")
    now_ms     = int(time.time() * 1000)
    # Approx lookback: limit * interval_minutes * 60 * 1000
    mins = int(resolution) * limit
    from_ms = now_ms - (mins * 60 * 1000)

    data = _get(
        f"{DEXSCREENER_CANDLES_URL}/{chain_id}/{pair_address}",
        params={"from": from_ms, "to": now_ms, "resolution": resolution},
        timeout=12,
    )
    if not data:
        return None
    candles = data.get("data", {}).get("ohlcv") if isinstance(data.get("data"), dict) else data.get("ohlcv")
    if not candles:
        # Try alternate key structure
        if isinstance(data, dict):
            for key in ("candles", "bars", "ohlcv", "data"):
                if isinstance(data.get(key), list) and data[key]:
                    candles = data[key]
                    break
    if not candles:
        return None

    result = []
    for c in candles:
        if isinstance(c, list) and len(c) >= 5:
            # [timestamp, open, high, low, close, volume?]
            result.append({
                "time":   c[0],
                "open":   float(c[1]),
                "high":   float(c[2]),
                "low":    float(c[3]),
                "close":  float(c[4]),
                "volume": float(c[5]) if len(c) > 5 else 0.0,
            })
        elif isinstance(c, dict):
            result.append({
                "time":   c.get("time") or c.get("t") or c.get("timestamp", 0),
                "open":   float(c.get("open")  or c.get("o", 0)),
                "high":   float(c.get("high")  or c.get("h", 0)),
                "low":    float(c.get("low")   or c.get("l", 0)),
                "close":  float(c.get("close") or c.get("c", 0)),
                "volume": float(c.get("volume") or c.get("v", 0)),
            })
    return result if result else None


# ─────────────────────────────────────────────────────────────────────────────
# BIRDEYE — OHLCV fallback (covers pump.fun + new Solana tokens)
# Free public endpoint, no API key required for basic OHLCV.
# ─────────────────────────────────────────────────────────────────────────────

BIRDEYE_OHLCV_URL = "https://public-api.birdeye.so/defi/ohlcv"

_BIRDEYE_INTERVAL = {
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "1h":  "1H",
    "4h":  "4H",
    "1d":  "1D",
}

def birdeye_get_ohlcv(mint: str, interval: str = "4h",
                       limit: int = 100) -> Optional[List[Dict]]:
    """
    Fetch OHLCV from Birdeye public API.
    Works for pump.fun tokens and any SPL token with trading activity.
    No API key needed for this endpoint.
    """
    birdeye_interval = _BIRDEYE_INTERVAL.get(interval, "4H")
    now_ts   = int(time.time())
    # Calculate interval in seconds for lookback
    interval_secs = {
        "1m": 60, "5m": 300, "15m": 900,
        "1h": 3600, "4h": 14400, "1d": 86400,
    }.get(interval, 14400)
    from_ts = now_ts - (interval_secs * limit)

    data = _get(
        BIRDEYE_OHLCV_URL,
        params={
            "address":        mint,
            "type":           birdeye_interval,
            "time_from":      from_ts,
            "time_to":        now_ts,
            "currency":       "usd",
        },
        timeout=12,
    )
    if not data:
        return None

    # Birdeye returns {"data": {"items": [...]}}
    items = None
    try:
        items = data.get("data", {}).get("items") or data.get("items") or []
    except Exception:
        return None

    if not items:
        return None

    result = []
    for c in items:
        try:
            result.append({
                "time":   int(c.get("unixTime", 0)) * 1000,  # → ms
                "open":   float(c.get("o") or c.get("open",  0)),
                "high":   float(c.get("h") or c.get("high",  0)),
                "low":    float(c.get("l") or c.get("low",   0)),
                "close":  float(c.get("c") or c.get("close", 0)),
                "volume": float(c.get("v") or c.get("volume", 0)),
            })
        except Exception:
            continue

    return result if len(result) >= 3 else None


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC CANDLES — built from DexScreener recent trades
# Last-resort fallback when no OHLCV endpoint has data (brand-new tokens).
# ─────────────────────────────────────────────────────────────────────────────

def dexscreener_build_synthetic_candles(pair_address: str, chain_id: str = "solana",
                                         interval: str = "4h") -> Optional[List[Dict]]:
    """
    Fetch recent trade data from DexScreener and aggregate into OHLCV candles.
    Used when no dedicated candle endpoint returns data (e.g. pump.fun tokens
    that are hours old).  Returns at least 3 candles or None.
    """
    # DexScreener trades endpoint
    data = _get(
        f"https://api.dexscreener.com/latest/dex/trades/{pair_address}",
        timeout=12,
    )
    if not data:
        return None

    trades = data if isinstance(data, list) else data.get("trades") or []
    if not trades:
        return None

    # interval_secs bucketing
    interval_secs = {
        "1m": 60, "5m": 300, "15m": 900,
        "1h": 3600, "4h": 14400, "1d": 86400,
    }.get(interval, 14400)

    # Build buckets: {bucket_start_ts: [prices]}
    buckets: Dict[int, list] = {}
    for t in trades:
        try:
            ts_s  = int(t.get("timestamp", 0) or 0)
            price = float(t.get("priceUsd") or 0)
            vol   = float(t.get("volumeUsd") or 0)
            if ts_s <= 0 or price <= 0:
                continue
            bucket = (ts_s // interval_secs) * interval_secs
            if bucket not in buckets:
                buckets[bucket] = []
            buckets[bucket].append((ts_s, price, vol))
        except Exception:
            continue

    if len(buckets) < 3:
        # Too few buckets — try smaller interval (1h) if we were asked for 4h
        if interval == "4h" and len(buckets) < 3:
            return dexscreener_build_synthetic_candles(pair_address, chain_id, "1h")
        if interval == "1h" and len(buckets) < 3:
            return dexscreener_build_synthetic_candles(pair_address, chain_id, "15m")
        return None

    result = []
    for bucket_ts in sorted(buckets.keys()):
        trades_in = buckets[bucket_ts]
        prices = [p for _, p, _ in trades_in]
        vols   = [v for _, _, v in trades_in]
        # Sort by timestamp to get true open/close
        ordered = sorted(trades_in, key=lambda x: x[0])
        result.append({
            "time":   bucket_ts * 1000,
            "open":   ordered[0][1],
            "close":  ordered[-1][1],
            "high":   max(prices),
            "low":    min(prices),
            "volume": sum(vols),
        })

    return result if len(result) >= 3 else None


# ─────────────────────────────────────────────────────────────────────────────
# BINANCE — Fallback for major tickers
# ─────────────────────────────────────────────────────────────────────────────

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
BINANCE_PRICE_URL  = "https://api.binance.com/api/v3/ticker/price"

_BINANCE_INTERVAL = {
    "1m": "1m", "5m": "5m", "15m": "15m",
    "1h": "1h", "4h": "4h", "1d":  "1d",
}

def binance_get_ohlcv(symbol: str, interval: str = "4h",
                      limit: int = 100) -> Optional[List[Dict]]:
    for pair in [f"{symbol.upper()}USDT", f"{symbol.upper()}USDC"]:
        data = _get(BINANCE_KLINES_URL, params={
            "symbol": pair,
            "interval": _BINANCE_INTERVAL.get(interval, "4h"),
            "limit": limit,
        })
        if not data or isinstance(data, dict):
            continue
        result = []
        for c in data:
            result.append({
                "time":   c[0],
                "open":   float(c[1]),
                "high":   float(c[2]),
                "low":    float(c[3]),
                "close":  float(c[4]),
                "volume": float(c[5]),
            })
        return result
    return None


def binance_get_price(symbol: str) -> Optional[float]:
    for pair in [f"{symbol.upper()}USDT", f"{symbol.upper()}USDC"]:
        data = _get(BINANCE_PRICE_URL, params={"symbol": pair})
        if data and "price" in data:
            return float(data["price"])
    return None


# ─────────────────────────────────────────────────────────────────────────────
# UNIFIED TOKEN RESOLVER
# ─────────────────────────────────────────────────────────────────────────────

class TokenInfo:
    """Resolved token info — everything the chart and price monitor needs."""
    def __init__(self,
                 mint: Optional[str],
                 symbol: str,
                 name: str,
                 chain: str,             # "solana" | "binance" | "unknown"
                 pair_address: Optional[str],
                 pair_chain_id: Optional[str],
                 current_price: Optional[float],
                 logo_uri: Optional[str] = None):
        self.mint         = mint
        self.symbol       = symbol
        self.name         = name
        self.chain        = chain
        self.pair_address = pair_address
        self.pair_chain_id = pair_chain_id
        self.current_price = current_price
        self.logo_uri     = logo_uri

    def __repr__(self):
        return (f"TokenInfo(symbol={self.symbol}, chain={self.chain}, "
                f"price={self.current_price}, pair={self.pair_address})")


def resolve_token(input_str: str) -> Optional[TokenInfo]:
    """
    Master resolver. Input can be:
      - A Solana contract address  → Jupiter + DexScreener
      - A ticker symbol            → Jupiter search → DexScreener search → Binance fallback

    Returns TokenInfo or None if not found.
    """
    raw = input_str.strip()

    # ── Path A: Solana CA ─────────────────────────────────────────────────
    if is_solana_ca(raw):
        return _resolve_by_ca(raw)

    # ── Path B: Symbol ────────────────────────────────────────────────────
    return _resolve_by_symbol(raw.upper())


def _resolve_by_ca(mint: str) -> Optional[TokenInfo]:
    """Resolve a Solana mint address."""
    # 1. Token metadata from Jupiter
    meta = jupiter_get_token_by_mint(mint)
    symbol   = (meta or {}).get("symbol", mint[:8] + "...")
    name     = (meta or {}).get("name",   symbol)
    logo_uri = (meta or {}).get("logoURI")

    # 2. Current price from Jupiter
    price = jupiter_get_price(mint)

    # 3. Best trading pair from DexScreener (for chart OHLCV)
    pair = dexscreener_get_pair(mint)
    pair_address  = (pair or {}).get("pairAddress")
    pair_chain_id = (pair or {}).get("chainId", "solana")

    # DexScreener price as fallback if Jupiter didn't resolve
    if price is None and pair:
        try:
            price = float(pair.get("priceUsd") or 0) or None
        except Exception:
            pass

    if price is None and pair is None:
        logger.warning(f"Could not resolve price or pair for CA {mint}")

    return TokenInfo(
        mint=mint,
        symbol=symbol,
        name=name,
        chain="solana",
        pair_address=pair_address,
        pair_chain_id=pair_chain_id,
        current_price=price,
        logo_uri=logo_uri,
    )


def _resolve_by_symbol(symbol: str) -> Optional[TokenInfo]:
    """Resolve by ticker symbol. Tries Jupiter → DexScreener → Binance."""

    # ── 1. Jupiter token list lookup (finds Solana tokens) ─────────────────
    jup_token = jupiter_search_by_symbol(symbol)
    if jup_token:
        mint = jup_token.get("address")
        if mint:
            info = _resolve_by_ca(mint)
            if info:
                return info

    # ── 2. DexScreener symbol search (catches any chain) ──────────────────
    pair = dexscreener_search_symbol(symbol)
    if pair:
        mint = pair.get("baseToken", {}).get("address")
        name = pair.get("baseToken", {}).get("name", symbol)
        try:
            price = float(pair.get("priceUsd") or 0) or None
        except Exception:
            price = None
        chain    = pair.get("chainId", "unknown")
        pair_addr = pair.get("pairAddress")
        return TokenInfo(
            mint=mint,
            symbol=symbol,
            name=name,
            chain=chain,
            pair_address=pair_addr,
            pair_chain_id=chain,
            current_price=price,
        )

    # ── 3. Binance fallback (BTC, ETH, SOL, etc.) ─────────────────────────
    price = binance_get_price(symbol)
    if price is not None:
        return TokenInfo(
            mint=None,
            symbol=symbol,
            name=symbol,
            chain="binance",
            pair_address=None,
            pair_chain_id=None,
            current_price=price,
        )

    return None


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC: get_current_price
# ─────────────────────────────────────────────────────────────────────────────

def get_current_price(input_str: str) -> Optional[float]:
    """
    Get current USD price for any token (CA or symbol).
    Used by price_monitor and /pnl command.
    """
    raw = input_str.strip()

    # Fast path: CA → Jupiter directly
    if is_solana_ca(raw):
        price = jupiter_get_price(raw)
        if price is not None:
            return price
        # Fallback to DexScreener pair price
        pair = dexscreener_get_pair(raw)
        if pair:
            try:
                return float(pair.get("priceUsd") or 0) or None
            except Exception:
                pass
        return None

    # Symbol path
    sym = raw.upper()

    # Try Jupiter token list → mint → Jupiter price
    jup_token = jupiter_search_by_symbol(sym)
    if jup_token:
        mint  = jup_token.get("address")
        price = jupiter_get_price(mint) if mint else None
        if price is not None:
            return price

    # DexScreener symbol search
    pair = dexscreener_search_symbol(sym)
    if pair:
        try:
            return float(pair.get("priceUsd") or 0) or None
        except Exception:
            pass

    # Binance last resort
    return binance_get_price(sym)


# ─────────────────────────────────────────────────────────────────────────────
# CHART RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def generate_chart(
    input_str: str,
    entry_price: Optional[float] = None,
    target: Optional[float] = None,
    stop_loss: Optional[float] = None,
    interval: str = "4h",
) -> Optional[io.BytesIO]:
    """
    Generate a styled candlestick chart.
    input_str can be a Solana CA or a ticker symbol.
    Returns BytesIO PNG or None on failure.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import matplotlib.patheffects as pe
        from matplotlib.gridspec import GridSpec
        import warnings
        warnings.filterwarnings("ignore")

        # ── Resolve token ─────────────────────────────────────────────────
        token = resolve_token(input_str)
        if token is None:
            logger.warning(f"Could not resolve token: {input_str}")
            return None

        # ── Fetch OHLCV ───────────────────────────────────────────────────
        candles = None

        if token.chain == "solana" and token.pair_address:
            # 1st try: DexScreener candle endpoint
            candles = dexscreener_get_ohlcv(
                token.pair_chain_id or "solana",
                token.pair_address,
                interval=interval,
                limit=100,
            )

            # 2nd try: Birdeye (covers pump.fun and new tokens DexScreener lacks candles for)
            if candles is None and token.mint:
                logger.debug(f"DexScreener candles empty for {token.mint}, trying Birdeye…")
                candles = birdeye_get_ohlcv(token.mint, interval=interval, limit=100)

            # 3rd try: Synthetic candles built from DexScreener trade history
            if candles is None:
                logger.debug(f"Birdeye empty for {token.mint}, building synthetic candles…")
                candles = dexscreener_build_synthetic_candles(
                    token.pair_address,
                    chain_id=token.pair_chain_id or "solana",
                    interval=interval,
                )

        if candles is None and token.chain != "solana":
            candles = binance_get_ohlcv(token.symbol, interval=interval, limit=100)

        if candles is None and token.pair_address and token.chain != "solana":
            # Last ditch DexScreener attempt for non-Solana pairs
            candles = dexscreener_get_ohlcv(
                token.pair_chain_id or "solana",
                token.pair_address,
                interval=interval,
                limit=100,
            )

        if not candles or len(candles) < 3:
            logger.warning(f"Insufficient candle data for {input_str}")
            return None

        # ── Compute EMAs ──────────────────────────────────────────────────
        closes = [c["close"] for c in candles]

        def ema(prices: list, span: int) -> list:
            k   = 2 / (span + 1)
            ema_vals = [prices[0]]
            for p in prices[1:]:
                ema_vals.append(p * k + ema_vals[-1] * (1 - k))
            return ema_vals

        ema20 = ema(closes, 20)
        ema50 = ema(closes, 50)

        # ── Colour palette ────────────────────────────────────────────────
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

        # ── Figure layout ─────────────────────────────────────────────────
        fig = plt.figure(figsize=(14, 8), facecolor=BG)
        gs  = GridSpec(4, 1, figure=fig, hspace=0.04)
        ax  = fig.add_subplot(gs[:3, 0])
        axv = fig.add_subplot(gs[3, 0], sharex=ax)

        for axis in [ax, axv]:
            axis.set_facecolor(BG)
            for spine in axis.spines.values():
                spine.set_color(GRID)
            axis.tick_params(colors=TEXT_C, labelsize=8)
            axis.yaxis.tick_right()

        plt.setp(ax.get_xticklabels(), visible=False)

        # ── Candles ───────────────────────────────────────────────────────
        for i, c in enumerate(candles):
            is_up    = c["close"] >= c["open"]
            color    = UP_C if is_up else DOWN_C
            body_bot = min(c["open"], c["close"])
            body_h   = abs(c["close"] - c["open"]) or (c["high"] - c["low"]) * 0.001

            ax.bar(i, body_h, bottom=body_bot, width=0.6,
                   color=color, linewidth=0, zorder=2)
            ax.plot([i, i], [c["low"], c["high"]],
                    color=color, linewidth=0.8, zorder=1)

            vol_color = VOL_UP if is_up else VOL_DOWN
            axv.bar(i, c["volume"], width=0.6, color=vol_color, linewidth=0)

        x = list(range(len(candles)))
        ax.plot(x, ema20, color=EMA20_C, linewidth=1.3, label="EMA 20", zorder=3)
        ax.plot(x, ema50, color=EMA50_C, linewidth=1.3, label="EMA 50", zorder=3)

        # ── Entry / Target / Stop lines ───────────────────────────────────
        legend_handles = [
            mpatches.Patch(color=EMA20_C, label="EMA 20"),
            mpatches.Patch(color=EMA50_C, label="EMA 50"),
        ]

        def price_label(p: float) -> str:
            if p >= 1000:
                return f"${p:,.2f}"
            elif p >= 1:
                return f"${p:,.4f}"
            elif p >= 0.0001:
                return f"${p:.6f}"
            else:
                return f"${p:.10f}"

        if entry_price:
            ax.axhline(entry_price, color=ENTRY_C, linewidth=1.5, linestyle="--", zorder=4)
            ax.text(len(candles) - 0.5, entry_price,
                    f"  Entry {price_label(entry_price)}",
                    color=ENTRY_C, fontsize=8, va="center", zorder=5)
            legend_handles.append(mpatches.Patch(color=ENTRY_C, label="Entry"))

        if target:
            ax.axhline(target, color=TARGET_C, linewidth=1.2, linestyle=":", zorder=4)
            ax.text(len(candles) - 0.5, target,
                    f"  Target {price_label(target)}",
                    color=TARGET_C, fontsize=8, va="center", zorder=5)
            legend_handles.append(mpatches.Patch(color=TARGET_C, label="Target"))

        if stop_loss:
            ax.axhline(stop_loss, color=STOP_C, linewidth=1.2, linestyle=":", zorder=4)
            ax.text(len(candles) - 0.5, stop_loss,
                    f"  Stop {price_label(stop_loss)}",
                    color=STOP_C, fontsize=8, va="center", zorder=5)
            legend_handles.append(mpatches.Patch(color=STOP_C, label="Stop"))

        ax.grid(True, color=GRID, linewidth=0.5, zorder=0)
        axv.grid(True, color=GRID, linewidth=0.5, axis="y", zorder=0)

        # ── X-axis labels (timestamps) ────────────────────────────────────
        step = max(1, len(candles) // 8)
        tick_positions = list(range(0, len(candles), step))
        axv.set_xticks(tick_positions)

        def fmt_ts(ts):
            try:
                from datetime import datetime, timezone
                t = ts / 1000 if ts > 1e10 else ts
                return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%m/%d %H:%M")
            except Exception:
                return ""

        axv.set_xticklabels(
            [fmt_ts(candles[i]["time"]) for i in tick_positions],
            rotation=30, ha="right", color=TEXT_C, fontsize=7
        )

        # ── Title ─────────────────────────────────────────────────────────
        current_price = closes[-1]
        prev_price    = closes[max(0, len(closes) - 7)]  # ~24h ago on 4h
        pct_change    = ((current_price - prev_price) / prev_price * 100) if prev_price else 0
        trend_emoji   = "📈" if pct_change >= 0 else "📉"
        sign          = "+" if pct_change >= 0 else ""

        # Display name: prefer symbol, truncate CA if needed
        display = token.symbol
        if len(display) > 20:
            display = display[:18] + "…"

        chain_tag = ""
        if token.chain == "solana":
            chain_tag = " • SOL"
        elif token.chain == "binance":
            chain_tag = ""
        elif token.chain:
            chain_tag = f" • {token.chain.upper()}"

        ax.set_title(
            f"{display}/USD{chain_tag}  •  {interval.upper()} Chart  •  "
            f"{price_label(current_price)}  {trend_emoji} {sign}{pct_change:.2f}%",
            color=TEXT_C, fontsize=11, fontweight="bold", pad=10
        )

        # Mint address sub-label (if CA)
        if is_solana_ca(input_str.strip()):
            mint_short = input_str.strip()[:6] + "…" + input_str.strip()[-6:]
            ax.text(0.5, 0.985, f"CA: {mint_short}",
                    transform=ax.transAxes, ha="center", va="top",
                    color="#4a5568", fontsize=7)

        ax.legend(
            handles=legend_handles, loc="upper left",
            facecolor=BG, edgecolor=GRID, labelcolor=TEXT_C, fontsize=8
        )

        # ── Watermark ─────────────────────────────────────────────────────
        fig.text(
            0.5, 0.015,
            "🤡 Call Channel Roast Bot  •  Claude made no mistake  •  Powered by Jupiter + DexScreener",
            ha="center", color="#30363d", fontsize=7.5, fontstyle="italic"
        )

        # ── Export ────────────────────────────────────────────────────────
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                    facecolor=BG, edgecolor="none")
        buf.seek(0)
        plt.close(fig)
        return buf

    except Exception as e:
        logger.error(f"Chart generation failed for {input_str}: {e}", exc_info=True)
        return None
