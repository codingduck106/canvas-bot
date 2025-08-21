import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
import threading, os
from flask import Flask
from datetime import datetime
from collections import defaultdict

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
    seen_ids = set()
    events_by_course = defaultdict(list)

    for token in CANVAS_TOKENS:
        headers = {"Authorization": f"Bearer {token.strip()}"}
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            events_by_course["⚠️ Errors"].append(f"Error {r.status_code}: {r.text}")
            continue

        events = r.json()
        for e in events:
            event_id = e.get("id")
            if event_id in seen_ids:
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

            events_by_course[course].append(f"• {title} — due {due_fmt}")

    return events_by_course if events_by_course else None

# ------------------- Manual command -------------------
@bot.command()
async def due(ctx):
    """Check upcoming assignments/events, grouped by course"""
    events_by_course = get_upcoming_events()

    if not events_by_course:
        await ctx.send("✅ No upcoming events found.")
        return

    # Build a nice formatted message
    lines = []
    for course, events in events_by_course.items():
        lines.append(f"📚 **{course}**")
        lines.extend(events)
        lines.append("")  # blank line between courses

    await ctx.send("\n".join(lines))

# ------------------- On ready -------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ------------------- Run bot -------------------
bot.run(DISCORD_TOKEN.strip())
