"""Publishes a Reel to the BiliNaKayo! Page using the official Facebook Graph API."""
import time
from pathlib import Path

import requests

import config

GRAPH = f"https://graph.facebook.com/{config.GRAPH_VERSION}"
UPLOAD = f"https://rupload.facebook.com/video-upload/{config.GRAPH_VERSION}"


class FacebookError(RuntimeError):
    pass


def _check(resp, what):
    try:
        data = resp.json()
    except ValueError:
        data = {"raw": resp.text[:300]}
    err = data.get("error") if isinstance(data, dict) else None
    if resp.status_code >= 400 or err:
        message = err.get("message") if isinstance(err, dict) else str(data)
        raise FacebookError(f"{what} failed ({resp.status_code}): {message}")
    return data


def _wait_until_uploaded(video_id, token, seconds=90):
    """Poll until Facebook says the file arrived. Carries on after the timeout; the publish step will report any problem."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            r = requests.get(f"{GRAPH}/{video_id}", params={"fields": "status", "access_token": token}, timeout=30)
            status = r.json().get("status", {}).get("video_status", "")
            if status in ("upload_complete", "ready"):
                return
        except Exception as exc:
            print(f"[facebook] status check hiccup: {exc}")
        time.sleep(4)


def publish_reel(video_path, description, title=None):
    """Upload and publish a Reel. Returns the video id."""
    token, page = config.FB_PAGE_TOKEN, config.FB_PAGE_ID
    if not token or not page:
        raise FacebookError("FB_PAGE_ID and FB_PAGE_TOKEN are not set")
    path = Path(video_path)
    size = path.stat().st_size

    # 1) start an upload session
    r = requests.post(f"{GRAPH}/{page}/video_reels", data={"upload_phase": "start", "access_token": token}, timeout=60)
    start = _check(r, "starting the upload")
    video_id = start["video_id"]
    upload_url = start.get("upload_url") or f"{UPLOAD}/{video_id}"

    # 2) send the video file
    with open(path, "rb") as fh:
        r = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {token}",
                "offset": "0",
                "file_size": str(size),
                "Content-Type": "application/octet-stream",
            },
            data=fh,
            timeout=300,
        )
    _check(r, "uploading the video")
    _wait_until_uploaded(video_id, token)

    # 3) publish it
    payload = {"upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED", "description": description, "access_token": token}
    if title:
        payload["title"] = title
    r = requests.post(f"{GRAPH}/{page}/video_reels", data=payload, timeout=60)
    _check(r, "publishing the reel")
    return video_id


def add_comment(video_id, message, tries=4):
    """Post the affiliate link as the first comment. Returns True on success."""
    for attempt in range(1, tries + 1):
        try:
            r = requests.post(
                f"{GRAPH}/{video_id}/comments",
                data={"message": message, "access_token": config.FB_PAGE_TOKEN},
                timeout=30,
            )
            _check(r, "posting the comment")
            return True
        except Exception as exc:
            print(f"[facebook] comment attempt {attempt}/{tries} failed: {exc}")
            time.sleep(8)  # a brand-new reel can take a few seconds before it accepts comments
    return False
