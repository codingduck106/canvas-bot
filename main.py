import os
import requests
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN")  # e.g. yourschool.instructure.com
CHANNEL_ID = int(str(os.getenv("CHANNEL_ID")))   # Discord channel ID to post in

# Discord bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fetch assignments from Canvas
def get_upcoming_assignments(days=7):
    now = datetime.utcnow()
    start_date = now.isoformat() + "Z"
    end_date = (now + timedelta(days=days)).isoformat() + "Z"

    url = f"https://{CANVAS_DOMAIN}/api/v1/calendar_events"
    params = {
        "type": "assignment",
        "start_date": start_date,
        "end_date": end_date
    }
    headers = {
        "Authorization": f"Bearer {CANVAS_TOKEN}"
    }

    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return [f"Error {r.status_code}: {r.text}"]

    events = r.json()
    assignments = []
    for e in events:
        due = e.get("start_at")
        due_fmt = datetime.fromisoformat(due.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC") if due else "No due date"
        assignments.append(f"📌 **{e['title']}** — due {due_fmt}")

    return assignments if assignments else ["No upcoming assignments found."]

# Manual command
@bot.command()
async def due(ctx, days: int = 7):
    """Check upcoming assignments"""
    assignments = get_upcoming_assignments(days)
    await ctx.send("\n".join(assignments))

# Auto daily reminder
@tasks.loop(hours=24)
async def daily_reminder():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        assignments = get_upcoming_assignments(7)
        message = "**📅 Assignments due in the next 7 days:**\n" + "\n".join(assignments)
        await channel.send(message) # type: ignore

@daily_reminder.before_loop
async def before_daily():
    await bot.wait_until_ready()
    # Schedule to run at a specific time UTC (e.g., 14:00 UTC = 7AM PT)
    now = datetime.utcnow()
    target = now.replace(hour=14, minute=0, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await discord.utils.sleep_until(target)

# Start the loop when bot runs
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    daily_reminder.start()

bot.run(DISCORD_TOKEN) # type: ignore
