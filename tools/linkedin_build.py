"""GitHub Actions helper: render LinkedIn graphics for any spec in instagram/linkedin/
that has no graphics yet (or whose spec changed since they were rendered).

Spec: instagram/linkedin/<date>.json (same shape as tools/linkedin_graphics.py, plus optional "image").
Output: ig/<date>/linkedin/sss-<date>-slide1.png and -slide2.png, plus a stamp of the spec it came from.
"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from linkedin_graphics import render

ROOT = Path(__file__).resolve().parent.parent
done = 0
for spec_path in sorted((ROOT / "instagram" / "linkedin").glob("*.json")):
    raw = spec_path.read_bytes()
    spec = json.loads(raw)
    out = ROOT / "ig" / spec["date"] / "linkedin"
    stamp = out / "spec.sha1"
    sha = hashlib.sha1(raw).hexdigest()
    if stamp.exists() and stamp.read_text().strip() == sha:
        continue
    render(spec, out)
    stamp.write_text(sha + "\n")
    print("Rendered", spec_path.name)
    done += 1
print(f"{done} spec(s) rendered")
