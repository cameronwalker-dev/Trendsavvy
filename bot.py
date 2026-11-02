# Trendsavvy: a personal AI assistant on Telegram, powered by Claude.
# Runs 24/7 on an AWS EC2 Ubuntu server as a systemd service.
# Keys are read from environment variables (see .env.example), never stored in code.

import os
import warnings
warnings.filterwarnings("ignore", module="yfinance")
import random
import datetime
from zoneinfo import ZoneInfo
import anthropic
from telegram import Update
from telegram.ext import (ApplicationBuilder, TypeHandler, ApplicationHandlerStop,
                          CommandHandler, MessageHandler, ContextTypes, filters)

claude = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY automatically
MODEL = "claude-haiku-5-5"      # small, low-cost model
TIMEZONE = ZoneInfo("America/Chicago")

SYSTEM_PROMPT = "You are a personal assistant. Keep replies short and practical."


def get_text(response):
    """Return the text part of Claude's reply, or a fallback if there isn't one."""
    return next((b.text for b in response.content if b.type == "text"), "Ran out of room, try again.")


def ask_claude(system, user_text, max_tokens=2000):
    response = claude.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_text}],
    )
    return get_text(response)


async def send_to_owner(context, text):
    await context.bot.send_message(chat_id=os.environ["MY_CHAT_ID"], text=text)


# ---------- Security: only the owner can use the bot ----------

async def owner_only(update, context):
    chat = update.effective_chat
    if chat is None or str(chat.id) != os.environ["MY_CHAT_ID"]:
        raise ApplicationHandlerStop  # silently ignore everyone else


# ---------- On-demand commands ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assistant online. Send me anything.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ask_claude(SYSTEM_PROMPT, update.message.text))


async def draft(update, context, style):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Type the command, then your message. Example: /pro can we move the meeting")
        return
    reply = ask_claude(f"Rewrite the user's message in a {style} tone. Return only the message, ready to send.", text)
    await update.message.reply_text(reply)


async def pro(update, context):
    await draft(update, context, "professional, polite, and clear")


async def casual(update, context):
    await draft(update, context, "casual, friendly, and relaxed")


def starters_text(topic):
    return ask_claude(
        "Give 3 fun, thoughtful conversation starters on the topic given. Number them. No intro. "
        "Make the first 2 short, under 12 words. Make the 3rd longer and more detailed.",
        f"Topic: {topic}",
    )


DEEP_THEMES = ["parenting style", "personal and shared goals", "marriage and commitment",
               "money and building a life together", "dreams and the future"]


async def starters(update, context):
    topic = " ".join(context.args) or "getting to know each other better"
    await update.message.reply_text(starters_text(topic))


async def datenight(update, context):
    await update.message.reply_text(starters_text("a fun, flirty date night with my partner"))


async def deeptalk(update, context):
    topic = " ".join(context.args) or random.choice(DEEP_THEMES)
    await update.message.reply_text(starters_text(f"deep, meaningful conversation with my partner about {topic}"))


SHOW_CATEGORIES = ["CIA operations, old and new", "physics", "trading and finance", "wars and military history",
                   "new technology", "medicine", "science discoveries", "whistleblowers",
                   "ancient history and lost civilizations", "space and the universe",
                   "psychology and the human mind", "secret societies and hidden history",
                   "conspiracies that turned out true"]


def make_show_topics(focus=""):
    if focus:
        request = f"Give 5 episode topic ideas about {focus}."
    else:
        picks = random.sample(SHOW_CATEGORIES, 5)
        request = "Give 5 episode topic ideas, one from each of these categories: " + ", ".join(picks)
    return ask_claude(
        "You help plan episodes for a weekly podcast about mind-opening topics. For each idea give a catchy "
        "title and one sentence on why it's fascinating. Stick to real, documented events and research, and say "
        "when something is disputed. Number them. No intro. Focus on events from 1914 to today, except ancient "
        "history and lost civilizations, which can be from any era.",
        request, max_tokens=4000,
    )


async def showtopics(update, context):
    await update.message.reply_text(make_show_topics(" ".join(context.args)))


def write_love_letter():
    return ask_claude(
        "Write a one-paragraph love letter from the user to their partner. Show appreciation for them, how much "
        "the user loves them, and how they want to grow together. Tone: smooth and confident, but sincere and "
        "straight from the heart. It should put them in a good mood. Make each one different. Return only the letter.",
        "Write this week's love letter.", max_tokens=4000,
    )


async def loveletter(update, context):
    await update.message.reply_text(write_love_letter())


# ---------- Market close report (no AI: pure math on Yahoo Finance data) ----------

def market_report():
    import yfinance as yf
    warnings.filterwarnings("ignore", module="yfinance")
    markets = {"Dow (US30)": "^DJI", "S&P 500": "^GSPC", "Nasdaq": "^IXIC"}
    lines = ["📈 Market Close Report"]
    for name, symbol in markets.items():
        try:
            data = yf.Ticker(symbol).history(period="5d")
            day = data.iloc[-1]
            prev_close = data.iloc[-2]["Close"]
            o, h, l, c = day["Open"], day["High"], day["Low"], day["Close"]
            change = c - prev_close
            pct = change / prev_close * 100
            rng = h - l
            body = abs(c - o)
            if rng > 0 and body <= rng * 0.1:
                verdict = "Doji – indecision, neither side won"
            elif c > o:
                verdict = "🟢 Buyers won the day"
            else:
                verdict = "🔴 Sellers won the day"
            arrow = "▲" if change >= 0 else "▼"
            date = data.index[-1].strftime("%a %b %d")
            lines.append(f"\n{name} – {date}\nClose {c:,.0f} {arrow} {change:+,.0f} ({pct:+.2f}%)\n"
                         f"Open {o:,.0f} | High {h:,.0f} | Low {l:,.0f} | Range {rng:,.0f}\n{verdict}")
        except Exception:
            lines.append(f"\n{name}: couldn't get data from Yahoo right now.")
    return "\n".join(lines)


async def market(update, context):
    await update.message.reply_text(market_report())


# ---------- Scheduled jobs ----------

async def weekly_starters(context):
    theme = random.choice(DEEP_THEMES)
    text = ("💬 This week's conversation starters\n\nDate night:\n"
            + starters_text("a fun, flirty date night with my partner")
            + f"\n\nDeep talk ({theme}):\n"
            + starters_text(f"deep, meaningful conversation with my partner about {theme}"))
    await send_to_owner(context, text)


async def weekly_love_letter(context):
    await send_to_owner(context, "💌 This week's love letter:\n\n" + write_love_letter())


async def weekly_showtopics(context):
    await send_to_owner(context, "🎙️ This week's podcast topic ideas:\n\n" + make_show_topics())


async def daily_market(context):
    await send_to_owner(context, market_report())


def main():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(TypeHandler(Update, owner_only), group=-1)

    for name, handler in [("start", start), ("pro", pro), ("casual", casual), ("starters", starters),
                          ("datenight", datenight), ("deeptalk", deeptalk), ("showtopics", showtopics),
                          ("loveletter", loveletter), ("market", market)]:
        app.add_handler(CommandHandler(name, handler))

    # Days: Sunday=0, Monday=1 ... Saturday=6 (Austin time)
    jobs = app.job_queue
    jobs.run_daily(weekly_starters, time=datetime.time(15, 0, tzinfo=TIMEZONE), days=(1,))
    jobs.run_daily(weekly_love_letter, time=datetime.time(7, 0, tzinfo=TIMEZONE), days=(3,))
    jobs.run_daily(weekly_showtopics, time=datetime.time(13, 0, tzinfo=TIMEZONE), days=(5,))
    jobs.run_daily(daily_market, time=datetime.time(15, 15, tzinfo=TIMEZONE), days=(1, 2, 3, 4, 5))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
