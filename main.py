from zoneinfo import ZoneInfo
from datetime import datetime
now = datetime.now(ZoneInfo("Asia/Manila"))

"""Picks the next product, makes the cartoon video, and posts it to the BiliNaKayo! Facebook Page.

Run by GitHub Actions every hour. You can also run it by hand:
    python main.py --sample --dry-run     # make a test video, post nothing
    python main.py --dry-run              # same, but with the next real product in the queue
    python main.py                        # the real thing
"""
import argparse
import sys
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

import captions
import config
import facebook
import products
import video

SAMPLE = {
    "platform": "Lazada",
    "title": "Portable Mini Blender USB Rechargeable Juice Cup 380ml",
    "price": "599",
    "image_url": "",
    "link": "https://example.com/your-affiliate-link",
    "notes": "",
}


def in_active_hours():
    start, end = (int(x) for x in config.ACTIVE_HOURS.split("-"))
    return start <= datetime.now(ZoneInfo(config.TIMEZONE)).hour < end


def run(args):
    if not args.dry_run and not args.force and not in_active_hours():
        print(f"Outside the active hours ({config.ACTIVE_HOURS}, Philippine time). Nothing to do.")
        return 0

    rows = products.load_queue()
    product = SAMPLE if args.sample else products.next_product(rows)
    if product is None:
        print("The product queue is empty. Add rows to data/products.csv (status 'ready').")
        return 0

    waiting = sum(products.is_ready(r) for r in rows)
    if not args.sample and waiting <= 5:
        print(f"WARNING: only {waiting} product(s) left in the queue. Add more soon.")

    if not product.get("image_url") and not args.sample:
        product["image_url"] = products.find_image(product["link"])

    print(f"Product: {product['title']}")
    copy = captions.make_copy(product)
    print("Hook:", copy["hook"])
    print("Voiceover:", copy["voiceover"])

    stamp = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%Y%m%d-%H%M")
    out = video.render(product, copy, config.OUTPUT_DIR / f"{stamp}.mp4")

    if args.dry_run:
        print("\nCaption that would be posted:\n" + copy["caption"])
        print(f"\nDry run finished. Video saved at {out}")
        return 0

    video_id = facebook.publish_reel(out, copy["caption"], title=copy["short_title"])
    print(f"Posted to Facebook (video id {video_id}).")

    products.mark_posted(product, video_id)  # save right away so a later hiccup can never cause a double post
    products.save_queue(rows)

    facebook.set_thumbnail(video_id, out.with_suffix(".jpg"))

    if not facebook.add_comment(video_id, f"Bili na kayo! 👉 {product['link']}"):
        print(f"WARNING: could not add the link comment. Add this link by hand: {product['link']}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="make the video but do not post or change the queue")
    parser.add_argument("--sample", action="store_true", help="use a built-in sample product")
    parser.add_argument("--force", action="store_true", help="ignore the active-hours setting")
    args = parser.parse_args()
    try:
        return run(args)
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
