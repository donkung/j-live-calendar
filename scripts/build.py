"""Inject parsed events into template.html and write site/index.html.

Usage: python scripts/build.py events.json
"""
import datetime, json, os, pathlib, re, sys


def analytics_snippet(code):
    """GoatCounter page-view counting, enabled by the GOATCOUNTER_CODE repo variable.

    Counts every page load (no cookies). The total is also shown under the title
    when "Allow adding visitor counts" is turned on in the GoatCounter settings.
    """
    if not code:
        return ""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,49}", code):
        sys.exit(f"GOATCOUNTER_CODE {code!r} is not a valid GoatCounter code (e.g. 'jlive-th').")
    base = f"https://{code}.goatcounter.com"
    return f"""<script data-goatcounter="{base}/count" async src="https://gc.zgo.at/count.v4.js"></script>
<script>
fetch("{base}/counter/TOTAL.json").then(r=>r.ok?r.json():null).then(d=>{{
  if(!d||!d.count) return;
  const el=document.getElementById("views"); el.textContent=" · "+d.count+" views"; el.hidden=false;
}}).catch(()=>{{}});
</script>"""

root = pathlib.Path(__file__).resolve().parent.parent
events = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if len(events) < 100:
    sys.exit(f"Only {len(events)} events parsed - refusing to publish (sheet layout may have changed).")

bkk = datetime.timezone(datetime.timedelta(hours=7))
updated = datetime.datetime.now(bkk).strftime("%-d %b %Y")

html = (root / "template.html").read_text(encoding="utf-8")
html = html.replace("__DATA__", json.dumps(events, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
html = html.replace("__UPDATED__", updated)
html = html.replace("__ANALYTICS__", analytics_snippet(os.environ.get("GOATCOUNTER_CODE", "").strip()))

out = root / "site"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
(out / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Built site/index.html with {len(events)} events ({updated})")
