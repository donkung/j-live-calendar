import csv, io, json, re, sys

MON = {m: i for i, m in enumerate(
    ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], 1)}

def mon(s):
    return MON.get(s.strip().lower()[:3])

def parse_date(s, year):
    """Return (start_iso, end_iso, extra_days list) or None."""
    s = s.strip().replace("\n", " ")
    # trailing explicit year (etc sheet)
    m = re.search(r"\s(\d{4})$", s)
    if m:
        year = int(m.group(1)); s = s[:m.start()].strip()
    if not s or s.startswith("?"):
        return None
    # "06-09, 13 Dec" style
    if "," in s:
        mm = re.match(r"(\d+)-(\d+),\s*(\d+)\s+(\w+)", s)
        if mm:
            mo = mon(mm.group(4))
            return (iso(year, mo, int(mm.group(1))), iso(year, mo, int(mm.group(2))), [iso(year, mo, int(mm.group(3)))])
    # chained ranges like "30-31 Aug-01 Sep" or "31 Oct - 1 Nov" or "29 Nov-01 Dec"
    parts = re.findall(r"(\d+)(?:\s*-\s*\d+)?\s*([A-Za-z]+)", s)
    days = re.findall(r"\d+", s)
    if not parts:
        mo = mon(s)
        if mo:  # month only ("Dec")
            return (iso(year, mo, 1), iso(year, mo, 1), [], True)
        return None
    first_mo = mon(parts[0][1]); last_mo = mon(parts[-1][1])
    if not first_mo or not last_mo:
        return None
    start = iso(year, first_mo, int(days[0]))
    end_day = int(re.findall(r"(\d+)\s*[A-Za-z]+\s*$", s)[0]) if re.search(r"\d+\s*[A-Za-z]+\s*$", s) else int(days[-1])
    end = iso(year, last_mo, end_day)
    return (start, end, [])

def iso(y, m, d):
    return f"{y:04d}-{m:02d}-{d:02d}"

LINK_RE = re.compile(r"\s*<<(https?://[^>]+)>>")

def split_link(s):
    """'Event <<https://x>>' -> ('Event', 'https://x'); plain URL -> ('', url)."""
    m = LINK_RE.search(s)
    if m:
        return LINK_RE.sub("", s).strip(), m.group(1)
    if s.startswith("http"):
        return "", s
    return s, ""

def strip_link(s):
    return LINK_RE.sub("", s).strip()

text = open(sys.argv[1], encoding="utf-8").read()
sheets = re.split(r"^## Sheet name: (.+)$", text, flags=re.M)
events = []
for i in range(1, len(sheets), 2):
    name, body = sheets[i].strip(), sheets[i + 1]
    ym = re.match(r"(\d{4})", name)
    year = int(ym.group(1)) if ym else None
    rows = list(csv.reader(io.StringIO(body.strip())))
    has_jp = False
    cur = None
    for r in rows:
        if not r or all(not c.strip() for c in r):
            continue
        if r[0].strip().lower() == "date":
            has_jp = len(r) > 2 and r[2] == ""
            continue
        if r[0] == "" and len(r) > 1 and r[1].startswith("http"):
            continue
        if len(r) == 1 and re.fullmatch(r"\d{4}", r[0].strip()):
            year = int(r[0]); continue
        r = r + [""] * 6
        if has_jp:
            date, artist, jp, venue, source, promoter = r[:6]
        else:
            date, artist, venue, source, promoter = r[:5]; jp = ""
        artist, jp, venue, source, promoter = [x.strip() for x in (artist, jp, venue, source, promoter)]
        artist, jp, venue, promoter = [strip_link(x) for x in (artist, jp, venue, promoter)]
        if date.strip():
            if year is None and not re.search(r"\d{4}", date):
                continue
            pd = parse_date(date, year)
            cur = None
            if not pd:
                continue
            title, link = split_link(source)
            cur = {"s": pd[0], "e": pd[1], "x": pd[2], "raw": date.strip(),
                   "t": title, "u": link, "v": venue, "p": promoter, "a": []}
            if len(pd) > 3: cur["approx"] = True
            events.append(cur)
            if artist: cur["a"].append([artist, jp])
        elif cur is not None:
            if artist: cur["a"].append([artist, jp])
            if venue and not cur["v"]: cur["v"] = venue
            if source:
                stext, slink = split_link(source)
                if slink and not cur["u"]:
                    cur["u"] = slink
                if not stext:
                    pass
                elif not cur["t"]:
                    cur["t"] = stext
                else:
                    cur["note"] = stext
events.sort(key=lambda e: e["s"])
for e in events:
    if not e["x"]: del e["x"]
    if e["e"] == e["s"]: del e["e"]
    for k in ("t", "u", "v", "p"):
        if not e[k]: del e[k]
    e["a"] = [a if a[1] else [a[0]] for a in e["a"]]
print(json.dumps(events, ensure_ascii=False, separators=(",", ":")))
print(len(events), "events", events[0]["s"], events[-1]["s"], file=sys.stderr)
