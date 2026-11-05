"""The product queue (data/products.csv) plus small helpers for prices and product images."""
import csv
import re
from datetime import datetime, timezone

import requests

import config

FIELDS = ["platform", "title", "price", "image_url", "link", "status", "posted_at", "fb_post_id", "notes"]
READY_STATUSES = ("", "ready", "new")  # anything else (posted, needs_link, skip...) is left alone


def load_queue():
    if not config.QUEUE_FILE.exists():
        return []
    with open(config.QUEUE_FILE, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    return [{k: (row.get(k) or "").strip() for k in FIELDS} for row in rows]


def save_queue(rows):
    with open(config.QUEUE_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def is_ready(row):
    return row["status"].lower() in READY_STATUSES and bool(row["title"]) and bool(row["link"])


def next_product(rows):
    """The first ready row in the file. Reorder the rows to change what posts next."""
    return next((r for r in rows if is_ready(r)), None)


def mark_posted(row, fb_post_id):
    row["status"] = "posted"
    row["posted_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row["fb_post_id"] = str(fb_post_id)


def find_image(link):
    """Best effort: read the product page's og:image. Many shops block bots, so this often returns ''."""
    try:
        r = requests.get(link, timeout=12, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        html = r.text
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.I) or re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I
        )
        return m.group(1) if m else ""
    except Exception as exc:
        print(f"[products] could not look up an image: {exc}")
        return ""


# --- price helpers ------------------------------------------------------------
def _amount(price):
    m = re.search(r"(\d[\d,]*\.?\d*)", price or "")
    if not m:
        return None
    value = float(m.group(1).replace(",", ""))
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"


def _is_usd(price):
    return "$" in price or "usd" in price.lower()


def price_label(price):
    """'599' -> '₱599'. Prices with a $ sign stay in dollars."""
    price = (price or "").strip()
    amount = _amount(price)
    if not price or not amount:
        return price
    return f"${amount}" if _is_usd(price) else f"₱{amount}"


def price_speech(price):
    """How the voiceover should say the price."""
    price = (price or "").strip()
    amount = _amount(price)
    if not price or not amount:
        return price
    return f"{amount.replace(',', '')} {'dollars' if _is_usd(price) else 'pesos'}"
