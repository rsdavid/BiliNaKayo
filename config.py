"""Settings for the BiliNaKayo! auto-poster.

Secrets (Facebook token, Claude key) are read from environment variables.
On GitHub they are stored under Settings > Secrets - never type them in this file.
"""
import random

# Original mascot characters (name, look, personality) used in the video script and visuals
CHARACTERS = [
    {"name": "Kayo",  "look": "a cheerful round chick in a tiny shopping bag", "voice_style": "excited"},
    {"name": "Mang Bili", "look": "a friendly sari-sari store uncle with a big smile", "voice_style": "warm"},
    {"name": "Ate Deals", "look": "a savvy girl with a bargain tag necklace", "voice_style": "upbeat"},
    {"name": "Boss Tipid", "look": "a chubby piggy bank wearing sunglasses", "voice_style": "cool"},
    {"name": "Lola Sulit", "look": "a sweet grandma holding a basket of finds", "voice_style": "gentle"},
]

# Background colors (hex) with a matching text color for readability
COLORS = [
    {"bg": "#FF6B6B", "text": "#FFFFFF"},  # coral
    {"bg": "#FFD93D", "text": "#222222"},  # sunny yellow
    {"bg": "#6BCB77", "text": "#FFFFFF"},  # fresh green
    {"bg": "#4D96FF", "text": "#FFFFFF"},  # sky blue
    {"bg": "#B983FF", "text": "#FFFFFF"},  # purple
    {"bg": "#FF9F45", "text": "#222222"},  # orange
]

def pick_look(avoid_last=None):
    """Return a random (character, color), avoiding repeating the last character."""
    pool = [c for c in CHARACTERS if c["name"] != avoid_last] or CHARACTERS
    return random.choice(pool), random.choice(COLORS)

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
QUEUE_FILE = DATA_DIR / "products.csv"

PAGE_NAME = "BiliNaKayo!"

# --- Facebook ---------------------------------------------------------------
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "").strip()
GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v26.0")

# --- Claude (writes the Taglish captions; optional - templates are used without it)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

# --- When to post (Philippine time) ------------------------------------------
TIMEZONE = "Asia/Manila"
# "6-24" means post from 6:00 AM up to 11:59 PM. Use "0-24" to post all day and night.
ACTIVE_HOURS = os.getenv("ACTIVE_HOURS") or "6-24"

# --- Voiceover ----------------------------------------------------------------
TTS_VOICE = os.getenv("TTS_VOICE", "fil-PH-BlessicaNeural")
TTS_RATE = os.getenv("TTS_RATE", "+8%")
TTS_PITCH = os.getenv("TTS_PITCH", "+8Hz")

# --- Video length limits (seconds) ----------------------------------------------
MIN_SECONDS = 5.0
MAX_SECONDS = 10.0
