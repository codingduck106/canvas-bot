import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
import threading, os
from flask import Flask
from datetime import datetime

# ------------------- Keep-alive server -------------------
app = Flask("keepalive")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run).start()

# ------------------- Load secrets -------------------
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN")  # e.g. yourschool.instructure.com
CHANNEL_ID = int(str(os.getenv("CHANNEL_ID")))   # Optional: for future use

# ------------------- Discord bot setup -------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------- Fetch upcoming events from Canvas -------------------
def get_upcoming_events():
    url = f"https://{CANVAS_DOMAIN}/api/v1/users/self/upcoming_events"
    headers = {
        "Authorization": f"Bearer {CANVAS_TOKEN.strip()}"  # Strip any accidental whitespace/newlines
    }

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return [f"Error {r.status_code}: {r.text}"]

    events = r.json()
    assignments = []
    for e in events:
        due = e.get("start_at")
        due_fmt = datetime.fromisoformat(due.replace("Z", "+00:00")).strftime(
            "%Y-%m-%d %H:%M UTC") if due else "No due date"
        title = e.get("title", "Untitled Event")
        assignments.append(f"📌 **{title}** — due {due_fmt}")

    return assignments if assignments else ["No upcoming events found."]

# ------------------- Manual command -------------------
@bot.command()
async def due(ctx):
    """Check upcoming assignments/events"""
    assignments = get_upcoming_events()
    await ctx.send("\n".join(assignments))

# ------------------- On ready -------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ------------------- Run bot -------------------
bot.run(DISCORD_TOKEN.strip())  # Strip to avoid accidental newline issues
