# Trendsavvy – Personal AI Assistant

A personal AI assistant on Telegram, built in Python with Anthropic's Claude API and running 24/7 on an AWS EC2 Linux server.

I built this as my first coding project while working full-time as a UPS driver and transitioning into cloud and network engineering.

## What it does

**On-demand commands**

| Command | What it does |
|---|---|
| `/pro <message>` | Rewrites a message in a professional tone |
| `/casual <message>` | Rewrites a message in a casual tone |
| `/starters <topic>` | 3 conversation starters on any topic |
| `/datenight` | 3 date-night conversation starters |
| `/deeptalk <theme>` | 3 deeper conversation starters (random theme if none given) |
| `/showtopics <focus>` | 5 podcast episode ideas |
| `/loveletter` | A one-paragraph love letter |
| `/market` | Market close report for the Dow, S&P 500, and Nasdaq |
| Any other text | Chat with the assistant |

**Scheduled jobs (Austin time)**
- Monday 3:00 PM – conversation starters
- Wednesday 7:00 AM – love letter
- Friday 1:00 PM – podcast topic ideas
- Weekdays 3:15 PM – market close report

## Market close report

Pulls daily data from Yahoo Finance with no AI involved, just math. For each index it shows open, high, low, close, change, and range, then classifies the day's candle:
- **Buyers won**: close above open
- **Sellers won**: close below open
- **Doji**: candle body is 10% or less of the day's range

## Tech stack

- **Python** – python-telegram-bot (with job queue), Anthropic SDK, yfinance
- **AWS EC2** – t3.micro instance running Ubuntu Linux
- **systemd** – runs the bot as a service: auto-starts on boot, restarts on crash
- **Linux tools** – SSH, SCP, nano, Python virtual environments

## Security

- **Owner-only access** – the bot silently ignores every chat except mine
- **No secrets in code** – keys live in a `.env` file (`chmod 600`) that is never committed
- **SSH locked to my IP** with key-pair login
- **AWS Budget alert** to catch unexpected costs

## Deployment (summary)

1. Launch an EC2 Ubuntu instance and connect over SSH
2. Copy `bot.py` to the server with SCP
3. Create a virtual environment and `pip install -r requirements.txt`
4. Create `.env` from `.env.example` and lock it with `chmod 600 .env`
5. Install `trendsavvy.service` to `/etc/systemd/system/` and run `sudo systemctl enable --now trendsavvy`

## What I learned

- Reading tracebacks to find the exact line and cause of an error
- Fixing real bugs: response-format errors, token limits, missing libraries, Python version issues
- How Linux servers, SSH, virtual environments, and systemd services work
- Building in small steps and testing each one (incremental development)
