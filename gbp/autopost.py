#!/usr/bin/env python3
"""
autopost.py - GNG Auto Detail Google Business Profile post helper.

Plain Python 3, no installs, so it runs the same in a cloud routine
(Claude Code, Codex) and on the Mac mini.

  python3 gbp/autopost.py plan                 is a post due? which town, which photo
  python3 gbp/autopost.py post --town "Madison" --photo interior-after.jpg --text "..." [--dry-run]
  python3 gbp/autopost.py list [N]             newest live posts

Google login, first match wins:
  1. env GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN  (cloud)
  2. ~/GNG/gng-gbp-auto2/token.json                           (Mac mini)
"""

import difflib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCOUNT = "100236051482222081839"
LOCATION = "4663363141070631568"
API = f"https://mybusiness.googleapis.com/v4/accounts/{ACCOUNT}/locations/{LOCATION}/localPosts"
PHOTO_BASE = "https://raw.githubusercontent.com/Gitandmaybehub/gng-auto-detail-images/main/gbp/photos/"
TOKEN_FILE = Path.home() / "GNG" / "gng-gbp-auto2" / "token.json"
PHONE = "862-204-7568"
MIN_HOURS = 40            # never post again sooner than this
ROTATION_START = "2026-09-28T00:00:00Z"   # photo rotation counts posts made after this
UTM = "utm_source=google&utm_medium=organic&utm_campaign=gbp_post"


# ---------- Google ----------

def access_token():
    cid, secret, refresh = (os.environ.get(k) for k in
                            ("GBP_CLIENT_ID", "GBP_CLIENT_SECRET", "GBP_REFRESH_TOKEN"))
    if not (cid and secret and refresh):
        if not TOKEN_FILE.exists():
            sys.exit("NO GOOGLE LOGIN: set GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN "
                     "in this environment, or run on the Mac mini.")
        t = json.loads(TOKEN_FILE.read_text())
        cid, secret, refresh = t["client_id"], t["client_secret"], t["refresh_token"]
    data = urllib.parse.urlencode({"client_id": cid, "client_secret": secret,
                                   "refresh_token": refresh, "grant_type": "refresh_token"}).encode()
    try:
        with urllib.request.urlopen("https://oauth2.googleapis.com/token", data, timeout=30) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"GOOGLE LOGIN FAILED ({e.code}): {e.read().decode()[:300]}\n"
                 "Christian has to re-authorize Google. Nothing was posted.")


def call(method, url, token, body=None):
    req = urllib.request.Request(url, method=method, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"GOOGLE ERROR {e.code} on {method}: {e.read().decode()[:800]}\nNothing was posted.")


def recent_posts(token, n=100):
    out, page = [], None
    while len(out) < n:
        q = {"pageSize": min(100, n - len(out))}
        if page:
            q["pageToken"] = page
        d = call("GET", API + "?" + urllib.parse.urlencode(q), token)
        out += d.get("localPosts", [])
        page = d.get("nextPageToken")
        if not page:
            break
    return out  # newest first


# ---------- picking ----------

def when(p):
    return datetime.strptime(p["createTime"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def towns():
    return json.loads((HERE / "towns.json").read_text())


def towns_named(text, names):
    """Town names in a post. Longest first, so 'Chester Township' is not also 'Chester'."""
    found, low = [], (text or "").lower()
    for name in sorted(names, key=len, reverse=True):
        pat = r"\b" + re.escape(name.lower()) + r"\b"
        if re.search(pat, low):
            found.append(name)
            low = re.sub(pat, " ", low)
    return found


def pick_town(posts):
    """The town that has gone longest without a mention. Never-used towns go first, in list order."""
    all_towns = towns()
    names = [t["town"] for t in all_towns]
    last_used = {}
    for i, p in enumerate(posts):              # i = 0 is the newest post
        for name in towns_named(p.get("summary"), names):
            last_used.setdefault(name, i)
    best = max(range(len(all_towns)),
               key=lambda k: (last_used.get(names[k], 10_000), -k))
    return all_towns[best]


def photos():
    return sorted(p.name for p in (HERE / "photos").iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))


def pick_photo(posts):
    """Rotate through every photo once before any repeats. Counts posts made since ROTATION_START."""
    start = datetime.fromisoformat(ROTATION_START.replace("Z", "+00:00"))
    n = sum(1 for p in posts if when(p) > start)
    files = photos()
    return files[n % len(files)]


# ---------- checks ----------

def check_text(text, town, recent=()):
    """Hard stops. Google removes posts with contact info in the text (rule updated 2026-09-25)."""
    problems = []
    if len(text) > 600:
        problems.append(f"too long ({len(text)} characters). Aim for 150 to 300")
    if len(text) < 100:
        problems.append("too short (under 100 characters)")
    if town.lower() not in text[:120].lower():
        problems.append(f"the town '{town}' is not in the first 120 characters")
    if re.search(r"[\u2014\u2013]", text):
        problems.append("has a long dash. Never use them")
    for m in re.findall(r"\$\s?\d[\d,.]*", text):
        if m.replace(" ", "") != "$20":
            problems.append(f"has a price ({m}). No prices in public posts")
    if re.search(r"\d[\d\s().-]{5,}\d", text):
        problems.append("has a phone number or long number. Google removes those. The button carries contact")
    if re.search(r"https?://|www\.|\.com\b|@", text, re.I):
        problems.append("has a link, email, or handle in the text. Google removes those")
    if "!!" in text or "??" in text:
        problems.append("has '!!'. One ! at a time")
    caps = [w for w in re.findall(r"\b[A-Z]{5,}\b", text)]
    if caps:
        problems.append(f"has ALL CAPS words ({', '.join(caps)})")
    if re.search(r"\b(it means the world|in today's|look no further|elevate|unleash|delve|nestled)\b", text, re.I):
        problems.append("has AI-sounding filler words")
    for old in recent:
        if difflib.SequenceMatcher(None, text.lower(), (old or "").lower()).ratio() > 0.75:
            problems.append("reads almost the same as a recent post. Write it fresh")
            break
    return problems


# ---------- commands ----------

def cmd_plan(token):
    posts = recent_posts(token)
    now = datetime.now(timezone.utc)
    hours = (now - when(posts[0])).total_seconds() / 3600 if posts else 999
    town = pick_town(posts)
    photo = pick_photo(posts)
    print(json.dumps({
        "due": hours >= MIN_HOURS,
        "hours_since_last_post": round(hours, 1),
        "rule": f"post only when {MIN_HOURS}+ hours have passed since the last post",
        "town": town["town"],
        "town_page": town["url"],
        "button_link": town["url"] + " (tracking tags are added by the post command)",
        "photo": photo,
        "photo_local_path": str(HERE / "photos" / photo),
        "photo_public_url": PHOTO_BASE + urllib.parse.quote(photo),
        "last_10_posts": [{"date": p["createTime"][:10], "text": p.get("summary", "")} for p in posts[:10]],
    }, indent=1, ensure_ascii=False))


def cmd_post(token, args):
    def arg(flag):
        return args[args.index(flag) + 1] if flag in args else None
    text, town, photo = arg("--text"), arg("--town"), arg("--photo")
    cta = (arg("--cta") or "LEARN_MORE").upper()
    if not (text and town and photo):
        sys.exit('Need --text "..." --town "Town" --photo file.jpg')
    match = [t for t in towns() if t["town"].lower() == town.lower()]
    if not match:
        sys.exit(f"'{town}' is not in towns.json. Only towns with a page on gngautodetail.com.")
    if photo not in photos():
        sys.exit(f"No photo '{photo}' in gbp/photos.")
    posts = recent_posts(token, 30)
    problems = check_text(text, match[0]["town"], [p.get("summary") for p in posts[:20]])
    if problems:
        sys.exit("NOT POSTED. Fix the text:\n- " + "\n- ".join(problems))

    hours = (datetime.now(timezone.utc) - when(posts[0])).total_seconds() / 3600 if posts else 999
    if hours < MIN_HOURS and "--force" not in args:
        sys.exit(f"NOT POSTED. Last post was {hours:.0f} hours ago. The rule is {MIN_HOURS}+ hours.")

    link = match[0]["url"] if cta == "LEARN_MORE" else "https://gngautodetail.com/book"
    tag = f'{UTM}&utm_content={datetime.now(timezone.utc):%Y-%m-%d}-{match[0]["url"].rsplit("/", 1)[-1]}'
    body = {
        "languageCode": "en-US",
        "topicType": "STANDARD",
        "summary": text,
        "callToAction": {"actionType": cta, "url": f"{link}?{tag}"},
        "media": [{"mediaFormat": "PHOTO", "sourceUrl": PHOTO_BASE + urllib.parse.quote(photo)}],
    }
    if "--dry-run" in args:
        print(json.dumps(body, indent=1, ensure_ascii=False))
        print("\nDRY RUN. Nothing was sent.")
        return
    d = call("POST", API, token, body)
    print(f"POSTED {d.get('state', '')} {d.get('createTime', '')}")
    print(d.get("searchUrl", d.get("name", "")))
    time.sleep(20)
    state = call("GET", "https://mybusiness.googleapis.com/v4/" + d["name"], token).get("state", "?")
    print(f"STATE AFTER 20 SECONDS: {state}")
    if state == "REJECTED":
        sys.exit("GOOGLE REJECTED THE POST. Remove the likely trigger and try once more.")


def cmd_list(token, n):
    for p in recent_posts(token, n):
        print(p["createTime"][:16].replace("T", " "), "UTC |", (p.get("summary") or "").replace("\n", " ")[:160])


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("plan", "post", "list"):
        sys.exit(__doc__)
    token = access_token()
    if a[0] == "plan":
        cmd_plan(token)
    elif a[0] == "post":
        cmd_post(token, a[1:])
    else:
        cmd_list(token, int(a[1]) if len(a) > 1 else 10)


if __name__ == "__main__":
    main()
