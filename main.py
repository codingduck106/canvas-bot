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
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN")  # e.g. yourschool.instructure.com

# Grab all CANVAS_TOKEN_x from env
CANVAS_TOKENS = [
    v for k, v in os.environ.items()
    if k.startswith("CANVAS_TOKEN") and v.strip()
]

# ------------------- Discord bot setup -------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------- Fetch upcoming events from Canvas -------------------
def get_upcoming_events():
    url = f"https://{CANVAS_DOMAIN}/api/v1/users/self/upcoming_events"
    assignments = []
    seen_ids = set()

    for token in CANVAS_TOKENS:
        headers = {"Authorization": f"Bearer {token.strip()}"}
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            assignments.append(f"⚠️ Error {r.status_code} for one account: {r.text}")
            continue

        events = r.json()
        for e in events:
            event_id = e.get("id")
            if event_id in seen_ids:  # skip duplicates
                continue
            seen_ids.add(event_id)

            title = e.get("title", "Untitled Event")
            course = e.get("context_name", "Unknown Course")
            due = e.get("start_at")
            if due:
                due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                due_fmt = due_dt.strftime("%B %d, %Y")
            else:
                due_fmt = "No due date"

            assignments.append(f"📌 **{title}** — **{course}** — due {due_fmt}")

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
bot.run(DISCORD_TOKEN.strip())
