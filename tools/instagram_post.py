"""Sport Sport Sport Instagram autopilot. Runs every 15 minutes from GitHub Actions.

    python3 tools/instagram_post.py plan     # prints what this run needs to do
    python3 tools/instagram_post.py render   # renders today's images, commits and pushes them
    python3 tools/instagram_post.py post     # posts anything that is due
    python3 tools/instagram_post.py status   # shows today's queue and what has posted

Schedule (Melbourne time): stories 8am weekdays; carousel Mon 7pm, Tue 7pm,
Wed 12pm, Thu 9am, Fri 6pm. Pause everything by creating instagram/PAUSE,
or one day by setting "hold": true in that day's queue file.
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
MEL = ZoneInfo("Australia/Melbourne")
# Images are served straight from GitHub so Instagram work never triggers a Netlify deploy (credits).
REPO = os.environ.get("GITHUB_REPOSITORY", "AngusJChisholm/sport-sport-sport")
IMG_BASE = f"https://raw.githubusercontent.com/{REPO}/main/ig"
# "facebook" = Instagram account linked to a Facebook Page (Page token, never expires).
# "instagram" = Instagram API with Instagram login (60-day token, refreshed weekly).
IG_LOGIN = os.environ.get("IG_LOGIN") or "facebook"
API_HOST = "https://graph.facebook.com/" if IG_LOGIN == "facebook" else "https://graph.instagram.com/"
API = API_HOST + os.environ.get("IG_API_VERSION", "v26.0")

STORY_TIME = dtime(8, 0)
STORY_CUTOFF = dtime(15, 0)   # don't post the morning stories later than this
FEED_TIMES = {0: dtime(19, 0), 1: dtime(19, 0), 2: dtime(12, 0), 3: dtime(9, 0), 4: dtime(18, 0)}
FEED_CUTOFF = dtime(23, 0)
RENDER_FROM = dtime(5, 30)


def now():
    override = os.environ.get("IG_NOW")  # for testing, e.g. 2026-10-14T19:05
    return datetime.fromisoformat(override).replace(tzinfo=MEL) if override else datetime.now(MEL)


def paths(date):
    return {
        "queue": ROOT / "instagram" / "queue" / f"{date}.json",
        "state": ROOT / "instagram" / "state" / f"{date}.json",
        "manifest": ROOT / "ig" / date / "manifest.json",
    }


def load(p, default=None):
    return json.loads(p.read_text()) if p.exists() else default


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def commit_push(message, *files):
    git("add", *[str(f) for f in files])
    if not git("status", "--porcelain"):
        return
    git("-c", "user.name=SSS Instagram bot", "-c", "user.email=actions@users.noreply.github.com",
        "commit", "-m", message + " [skip netlify]")
    for attempt in range(4):
        try:
            git("pull", "--rebase", "origin", "main")
            git("push", "origin", "HEAD:main")
            return
        except subprocess.CalledProcessError as e:
            print("push retry:", e.stderr.strip()[:200])
            time.sleep(5 * (attempt + 1))
    raise SystemExit("Could not push to main")


def story_window(q):
    """Stories go at 8am unless the queue sets "story_time" (e.g. "19:00" for a late first post)."""
    if q.get("story_time"):
        h, m = map(int, q["story_time"].split(":"))
        start = dtime(h, m)
        return start, dtime(min(h + 4, 23), 59)
    return STORY_TIME, STORY_CUTOFF


def plan():
    t = now()
    date = t.date().isoformat()
    p = paths(date)
    out = {"date": date, "render": False, "post": False, "reason": ""}
    if t.weekday() > 4:
        out["reason"] = "weekend"
    elif (ROOT / "instagram" / "PAUSE").exists():
        out["reason"] = "paused (instagram/PAUSE exists)"
    elif not p["queue"].exists():
        out["reason"] = "no queue file for today yet"
    else:
        state = load(p["state"], {})
        q = load(p["queue"])
        rendered = p["manifest"].exists() and load(p["manifest"]).get("queue_mtime") == q_stamp(p["queue"])
        out["render"] = t.time() >= RENDER_FROM and not rendered
        if q.get("hold"):
            out["reason"] = f"render={out['render']}, posting on hold today"
            return out
        s0, s1 = story_window(q)
        stories_due = q.get("stories") and not state.get("stories_done") and s0 <= t.time() < s1
        feed_due = not state.get("feed_done") and FEED_TIMES[t.weekday()] <= t.time() < FEED_CUTOFF
        out["post"] = bool(stories_due or feed_due)
        out["reason"] = f"render={out['render']} stories_due={bool(stories_due)} feed_due={bool(feed_due)}"
    return out


def q_stamp(qpath):
    import hashlib
    return hashlib.sha1(qpath.read_bytes()).hexdigest()[:12]


def do_render():
    sys.path.insert(0, str(ROOT / "tools"))
    from instagram_render import render
    date = now().date().isoformat()
    p = paths(date)
    manifest = render(date)
    manifest["queue_mtime"] = q_stamp(p["queue"])
    save(p["manifest"], manifest)
    commit_push(f"Instagram images for {date}", ROOT / "ig" / date)
    wait_live([f"{IMG_BASE}/{date}/manifest.json"], manifest)


def wait_live(urls, manifest=None, timeout=420):
    """Wait until GitHub serves the new images (Instagram fetches them from there)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            ok = True
            for u in urls:
                with urllib.request.urlopen(u + f"?v={int(time.time())}", timeout=20) as r:
                    if r.status != 200:
                        ok = False
                    if u.endswith("manifest.json") and manifest:
                        live = json.loads(r.read())
                        ok = ok and live.get("rendered_at") == manifest.get("rendered_at")
            if ok:
                print("Images are live")
                return True
        except Exception as e:
            print("waiting for deploy:", str(e)[:120])
        time.sleep(20)
    print("Images not live yet; will retry next run")
    return False


# ---------- Instagram Graph API ----------

def api(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:600]
        raise RuntimeError(f"Instagram API {e.code} on {path}: {body}")


def wait_container(cid, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = api("GET", cid, fields="status_code,status").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {cid} failed: {st}")
        time.sleep(5)
    raise RuntimeError(f"Container {cid} not ready after {timeout}s")


def publish(creation_id):
    return api("POST", f"{os.environ['IG_USER_ID']}/media_publish", creation_id=creation_id)["id"]


def clean_caption(text):
    text = (text or "").strip()
    tags = [w for w in text.split() if w.startswith("#")]
    if len(tags) > 30:
        for w in tags[30:]:
            text = text.replace(" " + w, "")
    return text[:2200]


def do_post():
    t = now()
    date = t.date().isoformat()
    p = paths(date)
    q = load(p["queue"])
    m = load(p["manifest"])
    if q.get("hold") or (ROOT / "instagram" / "PAUSE").exists():
        print("On hold, not posting")
        return
    if not m:
        print("Not rendered yet")
        return
    base = f"{IMG_BASE}/{date}"
    if not wait_live([f"{base}/manifest.json"], m, timeout=300):
        return
    uid = os.environ["IG_USER_ID"]
    state = load(p["state"], {"stories": {}})
    state.setdefault("stories", {})

    s0, s1 = story_window(q)
    if q.get("stories") and not state.get("stories_done") and s0 <= t.time() < s1:
        for name in m["stories"]:
            if name in state["stories"]:
                continue
            cid = api("POST", f"{uid}/media", media_type="STORIES", image_url=f"{base}/{name}")["id"]
            wait_container(cid)
            state["stories"][name] = publish(cid)
            save(p["state"], state)
            print("Posted story", name)
            time.sleep(3)
        state["stories_done"] = t.isoformat(timespec="minutes")
        save(p["state"], state)
        commit_push(f"Instagram stories posted {date}", p["state"])

    if not state.get("feed_done") and FEED_TIMES[t.weekday()] <= t.time() < FEED_CUTOFF:
        children = []
        for name in m["feed"][:10]:
            cid = api("POST", f"{uid}/media", image_url=f"{base}/{name}", is_carousel_item="true")["id"]
            children.append(cid)
        for cid in children:
            wait_container(cid)
        parent = api("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(children),
                     caption=clean_caption(q.get("caption")))["id"]
        wait_container(parent)
        state["feed_id"] = publish(parent)
        state["feed_done"] = t.isoformat(timespec="minutes")
        save(p["state"], state)
        print("Posted carousel", state["feed_id"])
        commit_push(f"Instagram carousel posted {date}", p["state"])

    try:
        maybe_refresh_token()
    except Exception as e:
        print("Token refresh failed (posting still worked):", str(e)[:300])


def maybe_refresh_token():
    """Long-lived Instagram tokens last 60 days. Refresh weekly and store the new one as a repo secret."""
    if IG_LOGIN == "facebook":
        return  # Page tokens from a long-lived user token don't expire
    marker = ROOT / "instagram" / "state" / "token.json"
    info = load(marker, {})
    last = info.get("refreshed")
    if last and datetime.fromisoformat(last) > now() - timedelta(days=7):
        return
    if not os.environ.get("GH_PAT"):
        print("No GH_PAT secret, skipping token refresh (token must be renewed by hand within 60 days)")
        return
    q = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": os.environ["IG_ACCESS_TOKEN"]})
    with urllib.request.urlopen(f"https://graph.instagram.com/refresh_access_token?{q}", timeout=60) as r:
        new = json.loads(r.read())["access_token"]
    subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--repo", os.environ["GITHUB_REPOSITORY"], "--body", new],
                   check=True, env={**os.environ, "GH_TOKEN": os.environ["GH_PAT"]})
    save(marker, {"refreshed": now().isoformat(timespec="minutes")})
    commit_push("Instagram token refreshed", marker)
    print("Token refreshed")


def check():
    """Connection test: reads the account and makes (but never publishes) one image container."""
    out = {"at": now().isoformat(timespec="minutes"), "login": IG_LOGIN}
    try:
        uid = os.environ["IG_USER_ID"]
        out["account"] = api("GET", uid, fields="username,name,followers_count")
        out["publishing_limit"] = api("GET", f"{uid}/content_publishing_limit", fields="quota_usage,config")
        sample = f"{IMG_BASE}/2026-10-13/feed-1.jpg"
        cid = api("POST", f"{uid}/media", image_url=sample)["id"]
        wait_container(cid, timeout=120)
        out["dry_run_container"] = "FINISHED (not published)"
        out["ok"] = True
    except Exception as e:
        out["ok"] = False
        out["error"] = str(e)[:800]
    print(json.dumps(out, indent=1))
    p = ROOT / "instagram" / "state" / "check.json"
    save(p, out)
    commit_push("Instagram connection check", p)


def status():
    date = now().date().isoformat()
    p = paths(date)
    print(json.dumps({"plan": plan(), "state": load(p["state"], {}), "manifest": load(p["manifest"], {})}, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "plan":
        result = plan()
        print(result["reason"])
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"render={str(result['render']).lower()}\npost={str(result['post']).lower()}\n")
    elif cmd == "render":
        do_render()
    elif cmd == "post":
        do_post()
    elif cmd == "check":
        check()
    else:
        status()
