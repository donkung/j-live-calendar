"""Inject parsed events into template.html and write site/index.html.

Usage: python scripts/build.py events.json
"""
import datetime, json, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
events = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if len(events) < 100:
    sys.exit(f"Only {len(events)} events parsed - refusing to publish (sheet layout may have changed).")

bkk = datetime.timezone(datetime.timedelta(hours=7))
updated = datetime.datetime.now(bkk).strftime("%-d %b %Y")

html = (root / "template.html").read_text(encoding="utf-8")
html = html.replace("__DATA__", json.dumps(events, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
html = html.replace("__UPDATED__", updated)

out = root / "site"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
(out / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Built site/index.html with {len(events)} events ({updated})")
