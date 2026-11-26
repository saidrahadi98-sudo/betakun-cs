"""Betakun CS on Discord. Run:  python discord_bot.py   (the bot is online only while this runs).

Two ways to use it:
  - type any message in the #betakun-cs channel (or mention the bot)
  - use the slash command  /betakun pertanyaan:<your question>  in any channel
"""
import asyncio
import os
import re

import discord
from discord import app_commands
from dotenv import load_dotenv

from src.answer import ask
from src.format_reply import format_reply

load_dotenv(override=True)
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("DISCORD_TOKEN is missing in .env")

CHANNEL_NAME = "betakun-cs"  # the bot answers every message in this channel, or when mentioned
BUSY_MESSAGE = "Maaf, layanan sedang sibuk. Coba lagi sebentar ya."

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
_synced = False


async def get_reply(text):
    """Run ask() off the bot's event loop (it is slow) and format the result."""
    try:
        result = await asyncio.to_thread(ask, text)
        return format_reply(text, result)
    except Exception:
        return BUSY_MESSAGE


@client.event
async def on_ready():
    global _synced
    if not _synced:
        # Register /betakun in each server the bot is in. Per-server sync shows up right away.
        for guild in client.guilds:
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
        _synced = True
    print(f"Online as {client.user}. Slash command /betakun is ready. Press Ctrl+C to stop.")


@tree.command(name="betakun", description="Tanya layanan pelanggan BorneoNet")
@app_commands.describe(pertanyaan="Tulis pertanyaanmu (Indonesia, bahasa gaul, campuran Inggris, atau Banjar)")
async def betakun(interaction: discord.Interaction, pertanyaan: app_commands.Range[str, 1, 500]):
    await interaction.response.defer(thinking=True)  # Discord gives only 3 seconds to respond
    question = pertanyaan.strip()
    reply = await get_reply(question)
    await interaction.followup.send(f"**Pertanyaan:** {question}\n\n{reply}"[:1900])


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
        reply = await get_reply(text)
    await message.reply(reply[:1900])  # Discord limit is 2000 characters


client.run(TOKEN)