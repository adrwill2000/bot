"""
bot.py — Call Channel Roast Bot 🤡
Main entry point. All Telegram command handlers live here.

Usage:
    python bot.py

Environment variables (or edit CONFIG block below):
    BOT_TOKEN   — Your BotFather token
    ADMIN_IDS   — Comma-separated Telegram user IDs with admin rights
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from functools import wraps
from typing import Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

from database import Database
from chart_generator import generate_chart, get_current_price, is_solana_ca, resolve_token
from pnl_card import generate_pnl_card
from price_monitor import PriceMonitor
from roasts import (
    get_call_roast, get_duplicate_roast, get_pnl_roast,
    get_spike_roast, get_trader_tier, get_extra_roast,
    EASTER_EGG_TRIGGER, EASTER_EGG_RESPONSE
)
from leaderboard import (
    encode_lb, decode_lb, build_keyboard, render_leaderboard,
    render_group_stats, render_head_to_head, render_network_stats,
    render_streak, render_top_coins,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG  (override via environment variables)
# ─────────────────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN",  "Bot token ID here")
ADMIN_IDS  = [
    int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()
]
SPIKE_THRESHOLD    = float(os.getenv("SPIKE_THRESHOLD", "50"))  # percent
MONITOR_INTERVAL   = int(os.getenv("MONITOR_INTERVAL",  "300")) # seconds

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database("calls.db")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("🚫 Admins only, chief.")
            return
        return await func(update, ctx)
    return wrapper


def user_mention(user_row: dict) -> str:
    """Returns @username or inline mention."""
    if user_row.get("username"):
        return f"@{user_row['username']}"
    uid  = user_row["user_id"]
    name = user_row.get("first_name", "Trader")
    return f"[{name}](tg://user?id={uid})"


def fmt_price(p: float) -> str:
    if p >= 1_000:
        return f"${p:,.2f}"
    elif p >= 1:
        return f"${p:,.4f}"
    else:
        return f"${p:,.8f}"


async def run_in_executor(func, *args):
    return await asyncio.get_event_loop().run_in_executor(None, func, *args)


def register_context(update: Update):
    """Auto-register group and user from any update. Call at the top of handlers."""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    # Always upsert user
    db.upsert_user(user.id, user.username or "", user.first_name or "Anon")
    # Register group if this is a group/supergroup/channel
    if chat.type in ("group", "supergroup", "channel"):
        db.upsert_group(
            chat_id=chat.id,
            title=chat.title or "Unknown",
            username=chat.username or "",
            chat_type=chat.type,
            registered_by=user.id,
        )


def get_chat_id(update: Update) -> int:
    """Return chat_id, or 0 for private chats."""
    chat = update.effective_chat
    if chat and chat.type in ("group", "supergroup", "channel"):
        return chat.id
    return 0


def parse_coin_input(raw: str) -> str:
    """
    Sanitise user coin input.
    - Solana CA (base58 32-44 chars): preserve exact case, strip $ and #
    - Everything else: uppercase, strip $ and #
    """
    clean = raw.strip().replace("$", "").replace("#", "")
    if is_solana_ca(clean):
        return clean          # preserve case — base58 is case-sensitive
    return clean.upper()


def token_display(coin: str, token_info=None) -> str:
    """
    Human-readable display label for a coin.
    If it's a CA and we have resolved token info, show SYMBOL (CA…).
    Otherwise just return the coin string.
    """
    if token_info and is_solana_ca(coin):
        sym = token_info.symbol
        short_ca = coin[:4] + "…" + coin[-4:]
        return f"{sym} `({short_ca})`"
    if is_solana_ca(coin):
        return f"`{coin[:6]}…{coin[-6:]}`"
    return coin


# ─────────────────────────────────────────────────────────────────────────────
# /start  /help
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤡 *CALL CHANNEL ROAST BOT* — Welcome to the Circus 🎪\n\n"
        "I document your financial decisions with the love and mockery they deserve.\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "*📞 Call Commands*\n"
        "`/call <COIN or CA> <entry> [target] [stop]` — Post a call\n"
        "`/close <COIN or CA> <exit_price>` — Close your call\n"
        "`/calls` — List all open calls\n"
        "`/mycalls` — Your open calls\n\n"
        "*📊 Stats & Leaderboards*\n"
        "`/leaderboard` — Group leaderboard (or global in DMs)\n"
        "`/gleaderboard` — 🌍 Global leaderboard\n"
        "`/shame` — Wall of Shame (group or DM)\n"
        "`/gshame` — 🌍 Global Wall of Shame\n"
        "`/groupstats` — This group's overall stats\n"
        "`/topcoins` — Most called coins here\n"
        "`/gtopcoins` — Most called coins globally\n"
        "`/h2h @user1 @user2` — Head-to-head battle\n"
        "`/streak` — Your current win/loss streak\n"
        "`/networkstats` — Global network stats\n"
        "`/mystats` — Your personal disaster report\n\n"
        "*🖼 Visual Commands*\n"
        "`/chart <COIN or CA> [1h/4h/1d]` — Chart via Jupiter + DexScreener\n"
        "`/pnl <COIN or CA>` — Live PnL card for open call\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "_Supports Solana contract addresses and ticker symbols._\n"
        "_Tip: Try typing_ `claude` _somewhere... 🥚_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# /call
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_call(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = ctx.args

    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/call <COIN or CA> <entry> [target] [stop]`\n"
            "Works with symbols: `/call SOL 150 180 130`\n"
            "Works with Solana CAs: `/call EPjFWdd5... 0.000012`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    coin = parse_coin_input(args[0])
    try:
        entry_price = float(args[1].replace(",", ""))
        target     = float(args[2].replace(",", "")) if len(args) > 2 else None
        stop_loss  = float(args[3].replace(",", "")) if len(args) > 3 else None
    except ValueError:
        await update.message.reply_text("❌ Invalid price format. Numbers only, no symbols.")
        return

    db.upsert_user(user.id, user.username or "", user.first_name or "Anon")
    register_context(update)
    chat_id  = get_chat_id(update)
    user_row = db.get_user(user.id)

    # Resolve token info (symbol/name for display when CA was given)
    token_info = None
    if is_solana_ca(coin):
        resolving_msg = await update.message.reply_text(
            f"🔍 Looking up token on Jupiter…"
        )
        token_info = await run_in_executor(resolve_token, coin)
        try:
            await resolving_msg.delete()
        except Exception:
            pass
        if token_info is None:
            await update.message.reply_text(
                f"❌ Couldn't find this token on Jupiter or DexScreener.\n"
                f"_Double-check the contract address — or the scam already rugged._"
            )
            return

    disp = token_display(coin, token_info)
    coin_label = token_info.symbol if token_info else coin  # for leaderboard/shame display

    # ── Duplicate detection ───────────────────────────────────────────────
    existing = db.get_open_call_for_coin(coin, chat_id)
    if existing and existing["user_id"] != user.id:
        orig_user = db.get_user(existing["user_id"])
        db.increment_duplicates(user.id, chat_id)
        db.increment_got_copied(existing["user_id"], chat_id)

        call_id = db.insert_call(
            user.id, coin, entry_price, target, stop_loss,
            is_duplicate=1, duplicate_of=existing["id"], chat_id=chat_id
        )

        roast = get_duplicate_roast(
            caller_name=user.first_name or "This person",
            original_name=orig_user.get("first_name", "the original caller"),
            coin=coin,
            original_price=existing["entry_price"],
            new_price=entry_price,
        )

        caption = (
            f"🚨 *DUPLICATE CALL DETECTED* 🚨\n\n"
            f"{user_mention(user_row)} just called {disp} at {fmt_price(entry_price)}\n"
            f"…but {user_mention(orig_user)} already called it at {fmt_price(existing['entry_price'])}\n\n"
            f"🤡 *Roast Panel:*\n{roast}\n\n"
            f"_Both users are now equally responsible for whatever happens. God help them._\n"
            f"_Call ID: #{call_id}_"
        )

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Chart", callback_data=f"chart_{coin}"),
            InlineKeyboardButton("🔥 Roast Again", callback_data=f"xroast_{call_id}"),
        ]])

        chart_buf = await run_in_executor(generate_chart, coin, entry_price, target, stop_loss)
        if chart_buf:
            await update.message.reply_photo(
                photo=chart_buf, caption=caption,
                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
            )
        else:
            await update.message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        return

    # ── Fresh call ────────────────────────────────────────────────────────
    call_id = db.insert_call(user.id, coin, entry_price, target, stop_loss, chat_id=chat_id)
    roast   = get_call_roast(user.first_name or "Anon", coin, entry_price, target, stop_loss)

    target_str = fmt_price(target) if target else "_none set (classic)_"
    stop_str   = fmt_price(stop_loss) if stop_loss else "_no stop (bold strategy)_"
    target_pct = f"  `({((target-entry_price)/entry_price*100):+.1f}%)`" if target else ""
    stop_pct   = f"  `({((stop_loss-entry_price)/entry_price*100):+.1f}%)`" if stop_loss else ""

    # Token metadata line (only for Solana CAs)
    meta_line = ""
    if token_info and is_solana_ca(coin):
        chain_str = token_info.chain.upper() if token_info.chain else "SOL"
        name_str  = f" — {token_info.name}" if token_info.name != token_info.symbol else ""
        meta_line = f"🔗 *Token:* `{token_info.symbol}`{name_str} | {chain_str}\n"
        if len(coin) > 10:
            meta_line += f"📋 *CA:* `{coin}`\n"

    caption = (
        f"📞 *NEW CALL* — {disp}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 *Caller:* {user_mention(user_row)}\n"
        f"{meta_line}"
        f"💰 *Entry:* `{fmt_price(entry_price)}`\n"
        f"🎯 *Target:* {target_str}{target_pct}\n"
        f"🛑 *Stop Loss:* {stop_str}{stop_pct}\n"
        f"🕐 *Time:* `{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC`\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🤡 {roast}\n\n"
        f"_Use `/close {coin} <price>` when done_\n"
        f"_Call ID: #{call_id}_"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("📊 Refresh Chart", callback_data=f"chart_{coin}"),
        InlineKeyboardButton("🔥 Roast Harder",  callback_data=f"xroast_{call_id}"),
        InlineKeyboardButton("📈 PnL Card",       callback_data=f"livepnl_{call_id}"),
    ]])

    chart_buf = await run_in_executor(generate_chart, coin, entry_price, target, stop_loss)
    if chart_buf:
        await update.message.reply_photo(
            photo=chart_buf, caption=caption,
            parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
    else:
        await update.message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


# ─────────────────────────────────────────────────────────────────────────────
# /close
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_close(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = ctx.args

    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/close BTC 70000`", parse_mode=ParseMode.MARKDOWN
        )
        return

    coin = parse_coin_input(args[0])
    try:
        exit_price = float(args[1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ Invalid price.")
        return

    open_call = db.get_user_open_call(user.id, coin)
    if not open_call:
        if user.id in ADMIN_IDS:
            open_call = db.get_open_call_for_coin(coin)
        if not open_call:
            disp_err = token_display(coin)
            await update.message.reply_text(f"❌ No open call found for {disp_err}.")
            return

    entry   = open_call["entry_price"]
    pnl_pct = ((exit_price - entry) / entry) * 100
    db.close_call(open_call["id"], exit_price, pnl_pct)

    caller  = db.get_user(open_call["user_id"])
    roast   = get_pnl_roast(caller.get("first_name", "Anon"), coin, pnl_pct)

    duration = datetime.utcnow() - datetime.fromisoformat(open_call["created_at"])
    hours    = max(0, int(duration.total_seconds() // 3600))
    emoji    = "🟢" if pnl_pct >= 0 else "🔴"
    disp     = token_display(coin)

    caption = (
        f"{emoji} *CALL CLOSED* — {disp}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 *Trader:* {user_mention(caller)}\n"
        f"📥 *Entry:* `{fmt_price(entry)}`\n"
        f"📤 *Exit:* `{fmt_price(exit_price)}`\n"
        f"💹 *PnL:* `{pnl_pct:+.2f}%`\n"
        f"⏱ *Duration:* `{hours}h`\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🤡 _{roast}_"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏆 Share PnL Card", callback_data=f"pnlcard_{open_call['id']}"),
        InlineKeyboardButton("📊 Chart",           callback_data=f"chart_{coin}"),
    ]])

    pnl_buf = await run_in_executor(
        generate_pnl_card,
        caller.get("first_name", "Anon"), coin, entry, exit_price, pnl_pct, hours, False
    )

    if pnl_buf:
        await update.message.reply_photo(
            photo=pnl_buf, caption=caption,
            parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
    else:
        await update.message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


# ─────────────────────────────────────────────────────────────────────────────
# LEADERBOARD  (context-aware: group by default, global in DMs or /gleaderboard)
# ─────────────────────────────────────────────────────────────────────────────

async def _send_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                             mode: str, scope: str, sort: str, period: str,
                             edit_message=None):
    """
    Core renderer used by both the command and the inline button callbacks.
    mode:   "top" | "shame"
    scope:  "group" | "global"
    sort:   "avg_pnl" | "win_rate" | "total_calls" | "best_call" | "total_pnl" | "consistency"
    period: "all" | "month" | "week" | "today"
    """
    register_context(update)
    chat_id    = get_chat_id(update)
    has_group  = chat_id != 0
    group_info = db.get_group(chat_id) if has_group else None
    group_title = (group_info["title"] if group_info else None) or "This Group"

    # Fetch rows
    if scope == "group" and has_group:
        if mode == "shame":
            rows = db.get_shame_group(chat_id, sort=sort, period=period)
        else:
            rows = db.get_leaderboard_group(chat_id, sort=sort, period=period)
    else:
        scope = "global"  # Normalise: can't do group scope in a DM
        if mode == "shame":
            rows = db.get_shame_global(sort=sort, period=period)
        else:
            rows = db.get_leaderboard_global(sort=sort, period=period)

    keyboard = build_keyboard(mode, scope, sort, period, chat_id, has_group)
    scope_label = group_title if scope == "group" else "🌍 Global"
    text, kb = render_leaderboard(rows, mode, scope, sort, period,
                                  group_title=scope_label, keyboard=keyboard)

    if edit_message:
        try:
            await edit_message.edit_text(text, parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=kb)
        except Exception:
            pass
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=kb)


async def cmd_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Auto-scopes to group if in a group, global if in DM."""
    chat_id = get_chat_id(update)
    scope   = "group" if chat_id else "global"
    await _send_leaderboard(update, ctx, mode="top", scope=scope,
                             sort="avg_pnl", period="all")


async def cmd_gleaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Explicit global leaderboard."""
    await _send_leaderboard(update, ctx, mode="top", scope="global",
                             sort="avg_pnl", period="all")


async def cmd_shame(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Wall of Shame — auto-scoped."""
    chat_id = get_chat_id(update)
    scope   = "group" if chat_id else "global"
    await _send_leaderboard(update, ctx, mode="shame", scope=scope,
                             sort="avg_pnl", period="all")


async def cmd_gshame(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Explicit global Wall of Shame."""
    await _send_leaderboard(update, ctx, mode="shame", scope="global",
                             sort="avg_pnl", period="all")


# ─────────────────────────────────────────────────────────────────────────────
# /mystats
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_mystats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    db.upsert_user(user.id, user.username or "", user.first_name or "Anon")
    stats = db.get_user_stats(user.id)

    if not stats or not stats.get("total_calls"):
        await update.message.reply_text(
            "📊 You haven't made any calls yet.\n_Honestly? Smart. The market hasn't had the pleasure of your capital._"
        )
        return

    avg    = stats["avg_pnl"] or 0
    best   = stats["best_call"] or 0
    worst  = stats["worst_call"] or 0
    total  = stats["total_calls"] or 0
    closed = stats["closed_calls"] or 0
    wins   = stats["wins"] or 0
    losses = stats["losses"] or 0
    dups   = stats["duplicates"] or 0
    copied = stats["got_copied"] or 0
    wr     = (wins / max(wins + losses, 1)) * 100
    tier   = get_trader_tier(avg, wr)
    name   = user.first_name or "Anon"

    lines = [
        f"📊 *Stats for {name}*",
        f"🎭 Tier: *{tier}*",
        f"━━━━━━━━━━━━━━━━━",
        f"📞 Total Calls: `{total}` (closed: `{closed}`)",
        f"✅ Wins: `{wins}`  |  ❌ Losses: `{losses}`",
        f"🎯 Win Rate: `{wr:.1f}%`",
        f"📈 Avg PnL: `{avg:+.2f}%`",
        f"🚀 Best Call: `{best:+.2f}%`",
        f"💀 Worst Call: `{worst:+.2f}%`",
    ]
    if dups:
        lines.append(f"🐑 Duplicate Calls: `{dups}` _(serial copycat behaviour on record)_")
    if copied:
        lines.append(f"👑 Times Copied: `{copied}` _(your influence is… questionable)_")
    if wr > 60:
        lines.append("\n_Statistically impressive. Statistically, coins also flip heads 10x in a row._")
    elif wr < 30:
        lines.append("\n_At this point the market might be actively avoiding your entries._")

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
        InlineKeyboardButton("🗑️ Wall of Shame", callback_data="shame"),
    ]])
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


# ─────────────────────────────────────────────────────────────────────────────
# /groupstats
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_groupstats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_context(update)
    chat_id = get_chat_id(update)
    if not chat_id:
        await update.message.reply_text(
            "ℹ️ `/groupstats` only works inside a group. In a DM, try `/networkstats`.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    group_info  = db.get_group(chat_id) or {}
    group_title = group_info.get("title", "This Group")
    summary     = db.get_group_summary(chat_id)
    top_coins   = db.get_top_coins_group(chat_id, limit=5)
    group_count = db.get_group_count()

    text = render_group_stats(summary, top_coins, group_title, group_count)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# /topcoins  /gtopcoins
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_topcoins(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_context(update)
    chat_id = get_chat_id(update)
    if chat_id:
        coins = db.get_top_coins_group(chat_id, limit=10)
        group = db.get_group(chat_id)
        label = (group["title"] if group else None) or "This Group"
    else:
        coins = db.get_top_coins_global(limit=10)
        label = "🌍 Global"
    text = render_top_coins(coins, label)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_gtopcoins(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    coins = db.get_top_coins_global(limit=10)
    text  = render_top_coins(coins, "🌍 Global")
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# /h2h  — Head-to-head
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_h2h(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_context(update)
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/h2h @user1 @user2`\n"
            "Compare two traders head to head.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    def clean(a: str) -> str:
        return a.lstrip("@").strip()

    uname_a = clean(args[0])
    uname_b = clean(args[1])
    chat_id = get_chat_id(update)

    with db._conn() as conn:
        row_a = conn.execute(
            "SELECT user_id FROM users WHERE username = ?", (uname_a,)
        ).fetchone()
        row_b = conn.execute(
            "SELECT user_id FROM users WHERE username = ?", (uname_b,)
        ).fetchone()

    if not row_a:
        await update.message.reply_text(f"❌ @{uname_a} not found. Have they made any calls?")
        return
    if not row_b:
        await update.message.reply_text(f"❌ @{uname_b} not found. Have they made any calls?")
        return

    h2h   = db.get_head_to_head(row_a["user_id"], row_b["user_id"], chat_id)
    group = db.get_group(chat_id) if chat_id else None
    label = (group["title"] if group else None) or ("🌍 Global" if not chat_id else "This Group")
    text  = render_head_to_head(h2h, label)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# /streak
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_streak(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_context(update)
    user    = update.effective_user
    chat_id = get_chat_id(update)
    streak  = db.get_streak(user.id, chat_id)
    text    = render_streak(user.first_name or "Anon", streak)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# /networkstats  — Global network overview (public-friendly)
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_networkstats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = db.get_network_stats()
    text  = render_network_stats(stats)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# /calls  /mycalls
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_calls(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    all_calls = db.get_all_open_calls()
    if not all_calls:
        await update.message.reply_text(
            "📋 No open calls right now.\n_Either everyone exited or nobody had the courage to call anything. Hard to say which is worse._"
        )
        return

    lines = [f"📋 *OPEN CALLS* ({len(all_calls)} total)\n"]
    for c in all_calls:
        caller = db.get_user(c["user_id"])
        name   = f"@{caller['username']}" if caller.get("username") else caller.get("first_name", "?")
        age    = datetime.utcnow() - datetime.fromisoformat(c["created_at"])
        hours  = int(age.total_seconds() // 3600)
        dup    = " _(copy)_" if c["is_duplicate"] else ""
        tgt    = f" → {fmt_price(c['target'])}" if c.get("target") else ""
        lines.append(f"• #{c['coin']} `{fmt_price(c['entry_price'])}`{tgt} | {name} | `{hours}h ago`{dup}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_mycalls(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user      = update.effective_user
    all_calls = db.get_all_open_calls()
    my_calls  = [c for c in all_calls if c["user_id"] == user.id]

    if not my_calls:
        await update.message.reply_text("📋 You have no open calls. Wisest decision you've made today.")
        return

    lines = [f"📋 *Your Open Calls*\n"]
    for c in my_calls:
        age   = datetime.utcnow() - datetime.fromisoformat(c["created_at"])
        hours = int(age.total_seconds() // 3600)
        tgt   = f" → {fmt_price(c['target'])}" if c.get("target") else ""
        stop  = f" | SL {fmt_price(c['stop_loss'])}" if c.get("stop_loss") else ""
        lines.append(f"• #{c['coin']} `{fmt_price(c['entry_price'])}`{tgt}{stop} | `{hours}h ago` | ID #{c['id']}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# /chart
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "❌ Usage: `/chart <COIN or CA> [interval]`\n"
            "Intervals: `1h` `4h` `1d` (default: `4h`)\n"
            "Example: `/chart SOL 1h` or `/chart EPjFWdd5…`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    coin     = parse_coin_input(ctx.args[0])
    interval = ctx.args[1].lower() if len(ctx.args) > 1 else "4h"
    if interval not in ("15m", "1h", "4h", "1d"):
        interval = "4h"

    disp = token_display(coin)
    msg  = await update.message.reply_text(f"📊 Fetching {interval} chart for {disp}…")
    chart_buf = await run_in_executor(generate_chart, coin, None, None, None, interval)

    if chart_buf:
        try:
            await msg.delete()
        except Exception:
            pass
        await update.message.reply_photo(
            photo=chart_buf,
            caption=f"📊 {disp} — {interval.upper()} Chart  •  via Jupiter + DexScreener",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await msg.edit_text(
            f"❌ Couldn't fetch chart for {disp}.\n"
            "_Token not found on Jupiter or DexScreener — check the address or it already rugged._"
        )


# ─────────────────────────────────────────────────────────────────────────────
# /pnl  — live PnL card for an open call
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_pnl(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not ctx.args:
        await update.message.reply_text(
            "❌ Usage: `/pnl <COIN or CA>`", parse_mode=ParseMode.MARKDOWN
        )
        return

    coin      = parse_coin_input(ctx.args[0])
    disp      = token_display(coin)
    open_call = db.get_user_open_call(user.id, coin)

    if not open_call:
        await update.message.reply_text(
            f"❌ No open call for {disp}.\n"
            f"_Can't generate a PnL card for a trade that doesn't exist. That would be fiction._"
        )
        return

    msg     = await update.message.reply_text(f"🔄 Fetching live price for {disp}…")
    current = await run_in_executor(get_current_price, coin)

    if not current:
        await msg.edit_text(
            f"❌ Couldn't fetch current price for {disp}.\n"
            "_Jupiter and DexScreener both came up empty. The scam may have already ended._"
        )
        return

    entry   = open_call["entry_price"]
    pnl_pct = ((current - entry) / entry) * 100
    duration = datetime.utcnow() - datetime.fromisoformat(open_call["created_at"])
    hours   = int(duration.total_seconds() // 3600)

    pnl_buf = await run_in_executor(
        generate_pnl_card,
        user.first_name or "Anon", coin, entry, current, pnl_pct, hours, True
    )

    caption = (
        f"📊 *Live PnL — {disp}*\n"
        f"Entry: `{fmt_price(entry)}` → Now: `{fmt_price(current)}`\n"
        f"PnL: `{pnl_pct:+.2f}%` over `{hours}h`"
    )

    if pnl_buf:
        await msg.delete()
        await update.message.reply_photo(
            photo=pnl_buf, caption=caption, parse_mode=ParseMode.MARKDOWN
        )
    else:
        await msg.edit_text(caption, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# INLINE BUTTON HANDLER
# ─────────────────────────────────────────────────────────────────────────────

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Chart button ─────────────────────────────────────────────────────
    if data.startswith("chart_"):
        coin      = data.split("_", 1)[1]
        disp      = token_display(coin)
        chart_buf = await run_in_executor(generate_chart, coin)
        if chart_buf:
            await query.message.reply_photo(
                photo=chart_buf,
                caption=f"📊 {disp} — 4H Chart  •  via Jupiter + DexScreener",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.message.reply_text("❌ Chart unavailable. Probably rugged.")

    # ── Extra roast button ────────────────────────────────────────────────
    elif data.startswith("xroast_"):
        call_id = int(data.split("_")[1])
        call    = db.get_call(call_id)
        if call:
            caller = db.get_user(call["user_id"])
            name   = caller.get("first_name", "This individual")
            roast  = get_extra_roast()
            await query.message.reply_text(
                f"🔥 *Extra Roast for {name}:*\n_{roast}_",
                parse_mode=ParseMode.MARKDOWN
            )

    # ── PnL card button (closed call) ────────────────────────────────────
    elif data.startswith("pnlcard_"):
        call_id = int(data.split("_")[1])
        call    = db.get_call(call_id)
        if call and call.get("exit_price"):
            caller  = db.get_user(call["user_id"])
            duration = (
                (datetime.fromisoformat(call["closed_at"]) -
                 datetime.fromisoformat(call["created_at"])).total_seconds() // 3600
                if call.get("closed_at") else 0
            )
            pnl_buf = await run_in_executor(
                generate_pnl_card,
                caller.get("first_name", "Anon"),
                call["coin"],
                call["entry_price"],
                call["exit_price"],
                call["pnl_pct"],
                int(duration),
                False
            )
            if pnl_buf:
                await query.message.reply_photo(
                    photo=pnl_buf,
                    caption=f"🏆 PnL Card — #{call['coin']} | `{call['pnl_pct']:+.2f}%`",
                    parse_mode=ParseMode.MARKDOWN
                )

    # ── Live PnL card button (open call) ──────────────────────────────────
    elif data.startswith("livepnl_"):
        call_id = int(data.split("_")[1])
        call    = db.get_call(call_id)
        if call:
            current = await run_in_executor(get_current_price, call["coin"])
            if current:
                entry   = call["entry_price"]
                pnl_pct = ((current - entry) / entry) * 100
                caller  = db.get_user(call["user_id"])
                duration = (datetime.utcnow() - datetime.fromisoformat(call["created_at"])).total_seconds() // 3600
                pnl_buf = await run_in_executor(
                    generate_pnl_card,
                    caller.get("first_name", "Anon"),
                    call["coin"], entry, current, pnl_pct, int(duration), True
                )
                if pnl_buf:
                    await query.message.reply_photo(
                        photo=pnl_buf,
                        caption=f"📡 *Live PnL* — #{call['coin']} `{pnl_pct:+.2f}%`",
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                await query.message.reply_text("❌ Couldn't fetch current price.")

    # ── Shortcut buttons from /mystats ────────────────────────────────────
    elif data == "leaderboard":
        await cmd_leaderboard(update, ctx)
    elif data == "shame":
        await cmd_shame(update, ctx)

    # ── Leaderboard navigation (lb:mode:scope:sort:period:chat_id) ─────────
    elif data.startswith("lb:"):
        try:
            mode, scope, sort, period, lb_chat_id = decode_lb(data)
            has_group = lb_chat_id != 0
            group_info = db.get_group(lb_chat_id) if has_group else None
            group_title = (group_info["title"] if group_info else None) or "This Group"

            if scope == "group" and has_group:
                rows = (db.get_shame_group(lb_chat_id, sort=sort, period=period)
                        if mode == "shame"
                        else db.get_leaderboard_group(lb_chat_id, sort=sort, period=period))
            else:
                scope = "global"
                rows = (db.get_shame_global(sort=sort, period=period)
                        if mode == "shame"
                        else db.get_leaderboard_global(sort=sort, period=period))

            keyboard   = build_keyboard(mode, scope, sort, period, lb_chat_id, has_group)
            scope_label = group_title if scope == "group" else "🌍 Global"
            text, kb   = render_leaderboard(rows, mode, scope, sort, period,
                                             group_title=scope_label, keyboard=keyboard)
            await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except Exception as e:
            logger.warning(f"Leaderboard callback error: {e}")
            await query.answer("Something went wrong. Try the command again.")


# ─────────────────────────────────────────────────────────────────────────────
# EASTER EGG — message handler
# ─────────────────────────────────────────────────────────────────────────────

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if EASTER_EGG_TRIGGER in update.message.text.lower():
        await update.message.reply_text(EASTER_EGG_RESPONSE, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# SPIKE ALERT CALLBACK  (called by PriceMonitor)
# ─────────────────────────────────────────────────────────────────────────────

async def send_spike_alert(
    app: Application,
    coin: str,
    entry_price: float,
    current_price: float,
    pnl_pct: float,
    caller_user_id: int,
    call_id: int,
    chat_id: int = 0,
):
    caller    = db.get_user(caller_user_id)
    name      = caller.get("first_name", "Someone")
    caller_mn = user_mention(caller)
    roast     = get_spike_roast(name, coin, pnl_pct)
    direction = "📈" if pnl_pct > 0 else "📉"

    caption = (
        f"🚨🔥 *SPIKE ALERT* — #{coin} {direction}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"Called by: {caller_mn}\n"
        f"📥 Entry: `{fmt_price(entry_price)}`\n"
        f"📡 Now: `{fmt_price(current_price)}`\n"
        f"💹 Move: `{pnl_pct:+.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🤡 _{roast}_\n\n"
        f"_Call ID #{call_id} — threshold: {SPIKE_THRESHOLD:.0f}%_"
    )

    chart_buf = await run_in_executor(generate_chart, coin, entry_price)

    # Determine destination: send to the group the call was made in.
    # If chat_id is 0 (call made in a DM / unknown), skip silently.
    if not chat_id:
        logger.warning(f"Spike alert for call #{call_id} has no chat_id — skipping send.")
        return

    try:
        if chart_buf:
            await app.bot.send_photo(
                chat_id=chat_id, photo=chart_buf,
                caption=caption, parse_mode=ParseMode.MARKDOWN
            )
        else:
            await app.bot.send_message(
                chat_id=chat_id, text=caption, parse_mode=ParseMode.MARKDOWN
            )
        logger.info(f"Spike alert sent to chat {chat_id} for #{coin} ({pnl_pct:+.1f}%)")
    except Exception as e:
        logger.error(f"Failed to send spike alert to chat {chat_id}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Set BOT_TOKEN in your environment or edit bot.py")
        return

    db.init()
    logger.info("✅ Database initialised")

    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start",        cmd_start))
    app.add_handler(CommandHandler("help",         cmd_start))
    app.add_handler(CommandHandler("call",         cmd_call))
    app.add_handler(CommandHandler("close",        cmd_close))
    app.add_handler(CommandHandler("leaderboard",  cmd_leaderboard))
    app.add_handler(CommandHandler("gleaderboard", cmd_gleaderboard))
    app.add_handler(CommandHandler("shame",        cmd_shame))
    app.add_handler(CommandHandler("gshame",       cmd_gshame))
    app.add_handler(CommandHandler("groupstats",   cmd_groupstats))
    app.add_handler(CommandHandler("topcoins",     cmd_topcoins))
    app.add_handler(CommandHandler("gtopcoins",    cmd_gtopcoins))
    app.add_handler(CommandHandler("h2h",          cmd_h2h))
    app.add_handler(CommandHandler("streak",       cmd_streak))
    app.add_handler(CommandHandler("networkstats", cmd_networkstats))
    app.add_handler(CommandHandler("mystats",      cmd_mystats))
    app.add_handler(CommandHandler("calls",        cmd_calls))
    app.add_handler(CommandHandler("mycalls",      cmd_mycalls))
    app.add_handler(CommandHandler("chart",        cmd_chart))
    app.add_handler(CommandHandler("pnl",          cmd_pnl))

    # Inline button handler
    app.add_handler(CallbackQueryHandler(button_handler))

    # Easter egg message handler (non-command messages)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Price monitor job
    monitor = PriceMonitor(db, app, send_spike_alert, spike_threshold=SPIKE_THRESHOLD)
    app.job_queue.run_repeating(
        monitor.check_prices,
        interval=MONITOR_INTERVAL,
        first=60,
        name="price_monitor"
    )

    logger.info(f"🤡 Call Channel Roast Bot starting — multi-group mode")
    logger.info(f"⚡ Spike threshold: {SPIKE_THRESHOLD:.0f}% | Monitor interval: {MONITOR_INTERVAL}s | Spike alerts go to originating group")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
