"""Writes the Taglish hook, voiceover and Facebook caption for a product."""
import json
import random
import re

import config
from products import price_label, price_speech

SYSTEM_PROMPT = """You write short, upbeat Taglish (Filipino + English mix) copy for "BiliNaKayo!", a Facebook page that shares shopping finds using affiliate links.

Return ONLY a JSON object with these keys:
- "hook": 2-5 words shown big on screen at the start. ALL CAPS. No emojis.
- "short_title": the product name in at most 6 words, plain and natural (not the keyword-stuffed listing title).
- "voiceover": one or two short spoken sentences, 12-16 words in total, casual Taglish. Say the product by its short name. No emojis, hashtags or symbols.
- "caption": the Facebook post text. 2-3 short lines in Taglish, up to 3 emojis, and a final line of 3-5 hashtags that includes #BiliNaKayo.

Strict rules:
- Use ONLY the facts in the product details you are given. Never invent features, discounts, ratings, sales numbers, stock levels, or "limited time" claims.
- Mention the price only if one was given.
- Honest, friendly tone. No false urgency.
- Say the link is in the comments; never paste a link yourself."""

HOOKS = ["BILI NA KAYO!", "TINGNAN MO 'TO!", "BAKA GUSTO MO 'TO!", "FIND OF THE DAY!", "SILIP LANG!"]

DISCLOSURE = "Link sa comments 👇 (affiliate link - may komisyon ang page, walang dagdag sa presyo mo)"


def _short_title(title, words=6):
    return " ".join(title.split()[:words])


def _template(product):
    """Plain fallback used when there is no Claude key or the call fails."""
    short = _short_title(product["title"])
    price = price_speech(product.get("price"))
    price_part = f" Presyo, {price}." if price else ""
    return {
        "hook": random.choice(HOOKS),
        "short_title": short,
        "voiceover": f"Tingnan mo 'to! {short}.{price_part} Check mo ang link sa comments!",
        "caption": f"Tingnan mo 'to! 🛒 {short}\nNasa comments ang link, check mo na!\n#BiliNaKayo #OnlineShopping #PinoyFinds",
    }


def _parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON found in reply")
    return json.loads(text[start : end + 1])


def _ask_claude(product):
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    details = {
        "platform": product.get("platform", ""),
        "title": product["title"],
        "price": price_label(product.get("price")),
        "notes": product.get("notes", ""),
    }
    msg = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "Product details:\n" + json.dumps(details, ensure_ascii=False)}],
    )
    data = _parse_json(msg.content[0].text)
    for key in ("hook", "short_title", "voiceover", "caption"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"missing '{key}' in Claude reply")
    return {k: data[k].strip() for k in ("hook", "short_title", "voiceover", "caption")}


def _finalize(copy):
    words = copy["voiceover"].split()
    if len(words) > 22:  # keep the voiceover inside the video length
        copy["voiceover"] = " ".join(words[:22])
    caption = copy["caption"]
    if not re.search(r"#ad\b", caption, re.IGNORECASE):
        caption += "\n#ad #affiliate"
    if "komisyon" not in caption.lower():
        caption = caption.replace("\n#", f"\n{DISCLOSURE}\n#", 1) if "\n#" in caption else caption + "\n" + DISCLOSURE
    copy["caption"] = caption
    return copy


def make_copy(product):
    copy = None
    if config.ANTHROPIC_API_KEY:
        try:
            copy = _ask_claude(product)
        except Exception as exc:  # never let a caption problem stop the posting
            print(f"[captions] Claude failed ({exc}); using template")
    if copy is None:
        copy = _template(product)
    return _finalize(copy)
