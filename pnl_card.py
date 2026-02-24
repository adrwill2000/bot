"""
pnl_card.py
Generates a beautiful, shareable PnL card image.
High-contrast dark theme with green/red glow effects.
Returns BytesIO PNG.
"""

import io
import logging
import math
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_pnl_card(
    name: str,
    coin: str,
    entry_price: float,
    exit_price: float,
    pnl_pct: float,
    duration_hours: int = 0,
    is_open: bool = False,
) -> Optional[io.BytesIO]:
    """
    Renders a PnL card.
    Green glow for profits, red glow for losses.
    Returns BytesIO PNG or None.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.patches import FancyBboxPatch
        import matplotlib.patheffects as pe
        import warnings
        warnings.filterwarnings("ignore")

        is_win = pnl_pct >= 0
        is_nuke = pnl_pct <= -30
        is_moon = pnl_pct >= 50

        # ── Palette ───────────────────────────────────────────────────────
        BG_DARK   = "#0a0e1a"
        BG_CARD   = "#111827"
        BORDER_C  = "#00e676" if is_win else "#ff1744"
        GLOW_C    = "#00e676" if is_win else "#ff1744"
        MAIN_TEXT = "#ffffff"
        SUB_TEXT  = "#94a3b8"
        PNL_C     = "#00e676" if is_win else "#ff1744"
        ACCENT    = "#60a5fa"
        DIVIDER   = "#1e293b"

        fig, ax = plt.subplots(figsize=(10, 5.6), facecolor=BG_DARK)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 5.6)
        ax.axis("off")

        # ── Background card ───────────────────────────────────────────────
        card = FancyBboxPatch((0.3, 0.3), 9.4, 5.0,
                               boxstyle="round,pad=0.1",
                               facecolor=BG_CARD,
                               edgecolor=BORDER_C, linewidth=2.5, zorder=1)
        ax.add_patch(card)

        # Glow effect — layered translucent borders
        for i, (lw, alpha) in enumerate([(6, 0.12), (10, 0.07), (16, 0.04)]):
            glow = FancyBboxPatch((0.3, 0.3), 9.4, 5.0,
                                   boxstyle="round,pad=0.1",
                                   facecolor="none",
                                   edgecolor=GLOW_C, linewidth=lw, alpha=alpha, zorder=0)
            ax.add_patch(glow)

        # ── Top left: coin + status ───────────────────────────────────────
        status_txt = "📡 OPEN POSITION" if is_open else ("✅ CLOSED WIN" if is_win else "❌ CLOSED LOSS")
        ax.text(0.7, 4.85, f"#{coin.upper()}/USDT", color=MAIN_TEXT, fontsize=22,
                fontweight="bold", va="top", zorder=5)
        ax.text(0.7, 4.25, status_txt, color=BORDER_C, fontsize=10,
                fontweight="bold", va="top", zorder=5)

        # ── Top right: trader name ────────────────────────────────────────
        ax.text(9.3, 4.85, name, color=ACCENT, fontsize=14,
                fontweight="bold", va="top", ha="right", zorder=5)
        if duration_hours > 0:
            ax.text(9.3, 4.38, f"⏱ {duration_hours}h held", color=SUB_TEXT, fontsize=9,
                    va="top", ha="right", zorder=5)

        # ── Divider ───────────────────────────────────────────────────────
        ax.plot([0.7, 9.3], [3.9, 3.9], color=DIVIDER, linewidth=1.5, zorder=5)

        # ── Center: BIG PnL number ────────────────────────────────────────
        sign = "+" if pnl_pct >= 0 else ""
        pnl_str = f"{sign}{pnl_pct:.2f}%"

        # Special labels for extreme results
        if is_moon:
            extra = "  🚀🌕"
        elif is_nuke:
            extra = "  💀"
        elif pnl_pct > 20:
            extra = "  🔥"
        elif pnl_pct < -10:
            extra = "  📉"
        else:
            extra = ""

        ax.text(5.0, 2.9, pnl_str + extra,
                color=PNL_C, fontsize=46, fontweight="bold",
                ha="center", va="center", zorder=5,
                path_effects=[
                    pe.withStroke(linewidth=4, foreground=BG_CARD),
                    pe.Normal()
                ])

        ax.text(5.0, 2.2, "PnL", color=SUB_TEXT, fontsize=11,
                ha="center", va="center", zorder=5)

        # ── Price row ─────────────────────────────────────────────────────
        ax.plot([0.7, 9.3], [1.75, 1.75], color=DIVIDER, linewidth=1.5, zorder=5)

        # Entry
        ax.text(2.0, 1.55, "ENTRY", color=SUB_TEXT, fontsize=9,
                ha="center", va="top", zorder=5)
        ax.text(2.0, 1.15, f"${entry_price:,.4f}", color=MAIN_TEXT, fontsize=13,
                fontweight="bold", ha="center", va="top", zorder=5)

        # Arrow
        arrow_color = PNL_C
        ax.annotate("", xy=(5.8, 1.25), xytext=(4.2, 1.25),
                    arrowprops=dict(arrowstyle="->", color=arrow_color, lw=2),
                    zorder=5)

        # Exit / Current
        exit_label = "CURRENT" if is_open else "EXIT"
        ax.text(7.5, 1.55, exit_label, color=SUB_TEXT, fontsize=9,
                ha="center", va="top", zorder=5)
        ax.text(7.5, 1.15, f"${exit_price:,.4f}", color=PNL_C, fontsize=13,
                fontweight="bold", ha="center", va="top", zorder=5)

        # ── Bottom bar: timestamp + branding ──────────────────────────────
        ax.plot([0.7, 9.3], [0.72, 0.72], color=DIVIDER, linewidth=1, zorder=5)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        ax.text(0.7, 0.58, timestamp, color=SUB_TEXT, fontsize=8, va="top", zorder=5)
        ax.text(9.3, 0.58, "🤡 Call Channel Roast Bot", color=SUB_TEXT, fontsize=8,
                ha="right", va="top", zorder=5, style="italic")

        # Subtle watermark in centre bottom
        ax.text(5.0, 0.38, "Claude made no mistake", color="#1e293b",
                fontsize=8, ha="center", va="top", zorder=5, style="italic")

        # ── Roast stripe on extreme losses ───────────────────────────────
        if is_nuke:
            ax.text(5.0, 0.05, "⚠️  NUCLEAR LOSS — SEEK PROFESSIONAL HELP  ⚠️",
                    color=DOWN_C if False else "#ff1744",
                    fontsize=9, ha="center", va="bottom", fontweight="bold", zorder=6)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor=BG_DARK, edgecolor="none")
        buf.seek(0)
        plt.close(fig)
        return buf

    except Exception as e:
        logger.error(f"PnL card generation failed: {e}")
        return None
