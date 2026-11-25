"""Betakun CS on Discord. Run:  python discord_bot.py   (the bot is online only while this runs)."""
import asyncio
import os
import re

import discord
from dotenv import load_dotenv

from src.answer import ask
from src.format_reply import format_reply

load_dotenv(override=True)
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("DISCORD_TOKEN is missing in .env")

CHANNEL_NAME = "betakun-cs"  # the bot answers every message in this channel, or when mentioned

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Online as {client.user}. Press Ctrl+C to stop.")


@client.event
async def on_message(message):
    if message.author.bot:
        return
    mentioned = client.user in message.mentions
    in_channel = getattr(message.channel, "name", "") == CHANNEL_NAME
    if not (mentioned or in_channel):
        return

    text = re.sub(r"<@!?\d+>", "", message.content).strip()
    if not text:
        return

    async with message.channel.typing():
        try:
            result = await asyncio.to_thread(ask, text)  # ask() is slow, keep it off the bot's event loop
            reply = format_reply(text, result)
        except Exception:
            reply = "Maaf, layanan sedang sibuk. Coba lagi sebentar ya."
    await message.reply(reply[:1900])  # Discord limit is 2000 characters


client.run(TOKEN)