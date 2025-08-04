# AI Image Telegram Bot

A Telegram bot that generates images using Stability AI and can add text or edit them.

## Features

- `/generate <prompt>` – Generate AI images
- `/text <text>` – Add text to images
- `/edit bg` – Remove background
- `/gibli` – Anime portrait
- `/replace` – Simulated face replace

## Requirements

- Python 3.9 or 3.10 recommended
- Environment variables:
  - `API_ID`
  - `API_HASH`
  - `BOT_TOKEN`
  - `STABILITY_API_KEY`

## Deployment

1. Clone repo to Render
2. Set Environment Variables
3. Set Start Command: `python bot.py`
4. Deploy!
