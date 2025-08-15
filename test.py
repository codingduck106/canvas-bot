import os
import requests

# Load env vars (Render's Environment tab — no .env locally needed)
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN")  # e.g., yourschool.instructure.com

print(f"CANVAS_TOKEN: {repr(CANVAS_TOKEN[:8] + '...' if CANVAS_TOKEN else None)}")
print(f"CANVAS_DOMAIN: {CANVAS_DOMAIN}")

if not CANVAS_TOKEN or not CANVAS_DOMAIN:
    print("❌ Missing CANVAS_TOKEN or CANVAS_DOMAIN environment variables!")
    exit(1)

# Try hitting the "current user" endpoint
url = f"https://{CANVAS_DOMAIN}/api/v1/users/self"
headers = {
    "Authorization": f"Bearer {CANVAS_TOKEN}"
}

print(f"Testing request to: {url}")

r = requests.get(url, headers=headers)

print(f"Status: {r.status_code}")
print(f"Response: {r.text}")

if r.status_code == 200:
    print("✅ Token is valid! Canvas API connection works.")
elif r.status_code == 401:
    print("❌ Invalid token or wrong domain.")
else:
    print("⚠️ Got an unexpected status code — check the domain and token.")
