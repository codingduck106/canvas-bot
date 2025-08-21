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
CANVAS_TOKEN_1 = os.getenv("CANVAS_TOKEN_1")
CANVAS_TOKEN_2 = os.getenv("CANVAS_TOKEN_2")
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN")  # e.g. yourschool.instructure.com

# ------------------- Discord bot setup -------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------- Fetch upcoming events from Canvas -------------------
def get_upcoming_events():
    # first cycle
    url = f"https://{CANVAS_DOMAIN}/api/v1/users/self/upcoming_events"
    headers = {
        "Authorization": f"Bearer {CANVAS_TOKEN_1.strip()}"  # Strip whitespace/newlines
    }

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return [f"Error {r.status_code}: {r.text}"]

    events = r.json()
    assignments = []

    for e in events:
        # Event title
        title = e.get("title", "Untitled Event")
        # Course/Class name (context_name)
        course = e.get("context_name", "Unknown Course")
        # Due date formatted
        due = e.get("start_at")
        if due:
            due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            due_fmt = due_dt.strftime("%B %d, %Y")  # e.g., August 21, 2025
        else:
            due_fmt = "No due date"

        assignments.append(f"📌 **{title}** — **{course}** — due {due_fmt}")

    headers2 = {
        "Authorization": f"Bearer {CANVAS_TOKEN_2.strip()}"
    }

    r2 = requests.get(url, headers=headers2)
    if r.status_code != 200:
        return [f"Error {r.status_code}: {r.text}"]

    events2 = r.json()
    for e in events2:
        # Event title
        title = e.get("title", "Untitled Event")
        # Course/Class name (context_name)
        course = e.get("context_name", "Unknown Course")
        # Due date formatted
        due = e.get("start_at")
        if due:
            due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            due_fmt = due_dt.strftime("%B %d, %Y")  # e.g., August 21, 2025
        else:
            due_fmt = "No due date"
        if f"📌 **{title}** — **{course}** — due {due_fmt}" not in assignments:
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

