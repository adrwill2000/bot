"""
leaderboard.py — All leaderboard rendering, formatting, and inline keyboard logic.

This module owns everything about how leaderboards look and navigate.
bot.py calls into here; nothing in here touches Telegram directly.

Scope:   "group" | "global"
Sort:    "avg_pnl" | "win_rate" | "total_calls" | "best_call" | "total_pnl" | "consistency"
Period:  "all" | "month" | "week" | "today"
Mode:    "top" (leaderboard) | "shame" (wall of shame)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from roasts import get_trader_tier


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

SORT_LABELS = {
    "avg_pnl":     "📊 Avg PnL",
    "win_rate":    "🎯 Win Rate",
    "total_calls": "📞 Most Active",
    "best_call":   "🚀 Best Call",
    "total_pnl":   "💰 Total PnL",
    "consistency": "🏅 Consistency",
}

PERIOD_LABELS = {
    "all":   "📅 All Time",
    "month": "🗓 Month",
    "week":  "📆 Week",
    "today": "☀️ Today",
}

MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
SHAME_TROPHIES = ["🏆💩", "🥈💩", "🥉💩", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK DATA ENCODING / DECODING
# ─────────────────────────────────────────────────────────────────────────────
# Format: lb:{mode}:{scope}:{sort}:{period}:{chat_id}
# Example: lb:top:group:avg_pnl:all:-1001234567890

def encode_lb(mode: str, scope: str, sort: str,
              period: str, chat_id: int) -> str:
    return f"lb:{mode}:{scope}:{sort}:{period}:{chat_id}"


def decode_lb(data: str) -> Tuple[str, str, str, str, int]:
    """Returns (mode, scope, sort, period, chat_id)."""
    parts = data.split(":")
    # chat_id might be negative (groups), so rejoin from index 5 onward
    return parts[1], parts[2], parts[3], parts[4], int(parts[5])


# ─────────────────────────────────────────────────────────────────────────────
# KEYBOARD BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_keyboard(mode: str, scope: str, sort: str,
                   period: str, chat_id: int,
                   has_group: bool = True) -> InlineKeyboardMarkup:
    """
    Build the full navigation keyboard for a leaderboard/shame board.
    Highlights the currently active button with a ✅ prefix.
    """
    def btn(label: str, b_mode: str, b_scope: str,
            b_sort: str, b_period: str) -> InlineKeyboardButton:
        active = (b_mode == mode and b_scope == scope
                  and b_sort == sort and b_period == period)
        prefix = "✅ " if active else ""
        return InlineKeyboardButton(
            prefix + label,
            callback_data=encode_lb(b_mode, b_scope, b_sort, b_period, chat_id)
        )

    rows = []

    # ── Row 1: Mode toggle ────────────────────────────────────────────────
    rows.append([
        btn("🏆 Leaderboard", "top",   scope, sort, period),
        btn("🗑️ Wall of Shame", "shame", scope, sort, period),
    ])

    # ── Row 2: Sort options (row 1) ───────────────────────────────────────
    rows.append([
        btn("📊 Avg PnL",      mode, scope, "avg_pnl",  period),
        btn("🎯 Win Rate",     mode, scope, "win_rate",  period),
        btn("🏅 Consistency",  mode, scope, "consistency", period),
    ])

    # ── Row 3: Sort options (row 2) ───────────────────────────────────────
    rows.append([
        btn("💰 Total PnL",   mode, scope, "total_pnl",   period),
        btn("🚀 Best Call",   mode, scope, "best_call",   period),
        btn("📞 Most Active", mode, scope, "total_calls", period),
    ])

    # ── Row 4: Period ─────────────────────────────────────────────────────
    rows.append([
        btn("📅 All Time", mode, scope, sort, "all"),
        btn("🗓 Month",    mode, scope, sort, "month"),
        btn("📆 Week",     mode, scope, sort, "week"),
        btn("☀️ Today",    mode, scope, sort, "today"),
    ])

    # ── Row 5: Scope (global / group) ─────────────────────────────────────
    scope_row = [btn("🌍 Global", mode, "global", sort, period)]
    if has_group and chat_id != 0:
        scope_row.append(btn("🏠 This Group", mode, "group", sort, period))
    rows.append(scope_row)

    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────────────────────────────────────
# LEADERBOARD RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_leaderboard(
    rows: List[Dict],
    mode: str,          # "top" | "shame"
    scope: str,         # "global" | "group"
    sort: str,
    period: str,
    group_title: Optional[str] = None,
    keyboard: Optional[InlineKeyboardMarkup] = None,
) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Render a leaderboard into a formatted Telegram message string.
    Returns (text, keyboard).
    """
    is_shame = (mode == "shame")
    trophies = SHAME_TROPHIES if is_shame else MEDALS

    # ── Header ────────────────────────────────────────────────────────────
    scope_label = group_title or "This Group" if scope == "group" else "🌍 Global"
    period_label = PERIOD_LABELS.get(period, "All Time")
    sort_label   = SORT_LABELS.get(sort, "Avg PnL")

    if is_shame:
        header = f"🗑️ *WALL OF SHAME*"
        subheader = "_a monument to financial creativity_"
        empty_msg = "Nobody has disgraced themselves sufficiently yet.\n_The wall is clean. For now._"
    else:
        header = f"🏆 *LEADERBOARD*"
        subheader = "_performance may not represent actual skill_"
        empty_msg = "No closed calls yet in this scope/period.\n_You're all equally untested and equally dangerous._"

    lines = [
        header,
        f"📍 {scope_label}  |  {period_label}  |  {sort_label}",
        f"_{subheader}_\n",
    ]

    if not rows:
        lines.append(empty_msg)
        return "\n".join(lines), keyboard

    for i, row in enumerate(rows):
        name  = f"@{row['username']}" if row.get("username") else row.get("first_name", "?")
        medal = trophies[i] if i < len(trophies) else f"{i+1}."

        avg_pnl = row.get("avg_pnl") or 0
        wr      = row.get("win_rate") or 0
        closed  = row.get("closed_calls") or 0
        best    = row.get("best_call") or 0
        worst   = row.get("worst_call") or 0
        total   = row.get("total_pnl") or 0
        cons    = row.get("consistency_score") or 0
        wins    = row.get("wins") or 0
        losses  = row.get("losses") or 0

        tier = get_trader_tier(avg_pnl, wr)

        # Primary stat (the sort column, always shown first and large)
        if sort == "avg_pnl":
            primary = f"`{avg_pnl:+.1f}%` avg"
        elif sort == "win_rate":
            primary = f"`{wr:.0f}%` WR"
        elif sort == "total_calls":
            primary = f"`{closed}` calls"
        elif sort == "best_call":
            primary = f"`{best:+.1f}%` best"
        elif sort == "worst_call":
            primary = f"`{worst:+.1f}%` worst"
        elif sort == "total_pnl":
            primary = f"`{total:+.1f}%` total"
        elif sort == "consistency":
            primary = f"`{cons:+.1f}` score"
        else:
            primary = f"`{avg_pnl:+.1f}%` avg"

        # Secondary stats line
        secondary = (
            f"Avg `{avg_pnl:+.1f}%` | WR `{wr:.0f}%` | "
            f"Calls `{closed}` | Best `{best:+.1f}%`"
        )

        lines.append(
            f"{medal} *{name}* — {tier}\n"
            f"    {primary}  •  {secondary}"
        )

    # ── Footer ────────────────────────────────────────────────────────────
    if is_shame:
        lines.append(
            "\n_These individuals have contributed generously to market liquidity._"
        )
    else:
        lines.append(
            "\n_Past performance is not indicative of future disasters._"
        )

    return "\n".join(lines), keyboard


# ─────────────────────────────────────────────────────────────────────────────
# GROUP STATS RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_group_stats(summary: Dict, top_coins: List[Dict],
                       group_title: str, group_count: int) -> str:
    avg    = summary.get("avg_pnl") or 0
    best   = summary.get("best_call") or 0
    worst  = summary.get("worst_call") or 0
    total  = summary.get("total_calls") or 0
    closed = summary.get("closed_calls") or 0
    opn    = summary.get("open_calls") or 0
    callers = summary.get("unique_callers") or 0
    dups   = summary.get("duplicates") or 0

    emoji = "🟢" if avg >= 0 else "🔴"

    lines = [
        f"📊 *GROUP STATS — {group_title}*",
        f"━━━━━━━━━━━━━━━━━",
        f"👥 Active Callers: `{callers}`",
        f"📞 Total Calls: `{total}` (closed `{closed}` | open `{opn}`)",
        f"{emoji} Group Avg PnL: `{avg:+.2f}%`",
        f"🚀 Best Call Ever: `{best:+.2f}%`",
        f"💀 Worst Call Ever: `{worst:+.2f}%`",
    ]
    if dups:
        lines.append(f"🐑 Duplicate Calls: `{dups}` _(this group has a sheep problem)_")

    if top_coins:
        lines.append("\n*🔥 Most Called Coins:*")
        for c in top_coins:
            coin_avg = c.get("avg_pnl")
            avg_str  = f" | avg `{coin_avg:+.1f}%`" if coin_avg is not None else ""
            wins     = c.get("wins") or 0
            losses   = c.get("losses") or 0
            lines.append(
                f"• #{c['coin']} — `{c['call_count']}` calls"
                f" | ✅`{wins}` ❌`{losses}`{avg_str}"
            )

    lines.append(f"\n_Bot is live in `{group_count}` group(s) globally._")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# HEAD-TO-HEAD RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_head_to_head(h2h: Dict, scope_label: str) -> str:
    def side(key: str) -> str:
        u     = h2h[key]
        name  = f"@{u['username']}" if u.get("username") else u.get("first_name", "?")
        avg   = u.get("avg_pnl") or 0
        best  = u.get("best_call") or 0
        worst = u.get("worst_call") or 0
        calls = u.get("closed_calls") or 0
        wins  = u.get("wins") or 0
        wr    = (wins / max(calls, 1)) * 100
        tier  = get_trader_tier(avg, wr)
        return (
            f"*{name}* — {tier}\n"
            f"    Avg `{avg:+.1f}%` | WR `{wr:.0f}%` | Calls `{calls}`\n"
            f"    Best `{best:+.1f}%` | Worst `{worst:+.1f}%`"
        )

    a_avg = h2h["user_a"].get("avg_pnl") or 0
    b_avg = h2h["user_b"].get("avg_pnl") or 0
    if a_avg > b_avg:
        verdict = f"🏆 Edge: *{h2h['user_a'].get('first_name', '?')}*"
    elif b_avg > a_avg:
        verdict = f"🏆 Edge: *{h2h['user_b'].get('first_name', '?')}*"
    else:
        verdict = "🤝 Dead even. Both equally mediocre."

    return (
        f"⚔️ *HEAD TO HEAD* — {scope_label}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{side('user_a')}\n\n"
        f"        🆚\n\n"
        f"{side('user_b')}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{verdict}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# NETWORK STATS RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_network_stats(stats: Dict) -> str:
    users   = stats.get("total_users") or 0
    groups  = stats.get("total_groups") or 0
    calls   = stats.get("total_calls") or 0
    closed  = stats.get("closed_calls") or 0
    avg     = stats.get("global_avg_pnl") or 0
    best    = stats.get("best_call_ever") or 0
    worst   = stats.get("worst_call_ever") or 0
    coins   = stats.get("unique_coins") or 0

    return (
        f"🌐 *NETWORK STATS*\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: `{users:,}`\n"
        f"🏠 Active Groups: `{groups:,}`\n"
        f"📞 Total Calls: `{calls:,}` (closed `{closed:,}`)\n"
        f"🪙 Unique Coins Called: `{coins}`\n"
        f"📈 Global Avg PnL: `{avg:+.2f}%`\n"
        f"🚀 Best Call Ever: `{best:+.2f}%`\n"
        f"💀 Worst Call Ever: `{worst:+.2f}%`\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"_Claude made no mistake building this._"
    )


# ─────────────────────────────────────────────────────────────────────────────
# STREAK RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_streak(name: str, streak: Dict) -> str:
    stype = streak.get("type")
    count = streak.get("count", 0)

    if not stype or count == 0:
        return f"📊 {name} has no closed calls yet. Streak: `0`."

    if stype == "win":
        bars = "🟢" * min(count, 10)
        if count >= 5:
            comment = "On an absolute heater. Don't ruin it."
        elif count >= 3:
            comment = "A winning streak! Quick, screenshot before it ends."
        else:
            comment = "Winning. For now."
        return (
            f"🔥 *{name}'s Streak*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"✅ Win streak: `{count}` {bars}\n"
            f"_{comment}_"
        )
    else:
        bars = "🔴" * min(count, 10)
        if count >= 5:
            comment = "At this point the market has a personal vendetta."
        elif count >= 3:
            comment = "The losses are doing some heavy lifting here."
        else:
            comment = "Losing streak. Could be worse. (It usually gets worse.)"
        return (
            f"💀 *{name}'s Streak*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"❌ Loss streak: `{count}` {bars}\n"
            f"_{comment}_"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TOP COINS RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_top_coins(coins: List[Dict], scope_label: str) -> str:
    if not coins:
        return "No coins called yet."

    lines = [
        f"🪙 *TOP COINS — {scope_label}*",
        f"_(most called, with results)_\n",
    ]
    for i, c in enumerate(coins):
        medal  = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
        avg    = c.get("avg_pnl")
        wins   = c.get("wins") or 0
        losses = c.get("losses") or 0
        total  = wins + losses
        avg_str = f" | avg `{avg:+.1f}%`" if avg is not None else " | _no closed calls_"
        wr_str  = f" | WR `{(wins/max(total,1)*100):.0f}%`" if total else ""
        lines.append(
            f"{medal} *#{c['coin']}* — `{c['call_count']}` calls"
            f" | ✅`{wins}` ❌`{losses}`{avg_str}{wr_str}"
        )
    return "\n".join(lines)
