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

STRIKE_RE = re.compile(r"~~(.*?)~~")

def marks(s):
    """Return (text, red, fully_struck, struck_parts) for one cell."""
    red = "[[red]]" in s
    s = s.replace("[[red]]", "").strip()
    parts = [p.strip() for p in STRIKE_RE.findall(s) if p.strip()]
    rest = STRIKE_RE.sub("", s).strip()
    full = bool(parts) and not LINK_RE.sub("", rest).strip()
    clean = STRIKE_RE.sub(r"\1", s).strip() if full else re.sub(r"\s{2,}", " ", rest)
    return clean, red, full, parts

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
        date, d_red, d_struck, _ = marks(date)
        artist, a_red, a_struck, _ = marks(artist)
        jp = marks(jp)[0]
        venue, _, v_struck, v_old = marks(venue)
        source = marks(source)[0]
        promoter = marks(promoter)[0]
        artist, jp, venue, source, promoter = [x.strip() for x in (artist, jp, venue, source, promoter)]
        artist, jp, venue, promoter = [strip_link(x) for x in (artist, jp, venue, promoter)]
        row_cancelled = d_red or d_struck if date.strip() else bool(cur and cur.get("c"))
        if row_cancelled:      # whole row struck through: the venue itself did not change
            v_old = []
        elif v_struck:         # only the venue struck: keep it as the old venue
            v_old, venue = [venue], ""
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
            if d_red or d_struck: cur["c"] = 1          # cancelled
            if v_old: cur["vo"] = ", ".join(v_old)       # venue changed from
            events.append(cur)
            if artist: cur["a"].append([artist, jp])
        elif cur is not None:
            if artist: cur["a"].append([artist, jp])
            if artist and (a_red or a_struck) and not cur.get("c"):
                cur.setdefault("wd", []).append(artist)  # artist dropped from the line-up
            if venue and not cur["v"]: cur["v"] = venue
            if v_old and not cur.get("vo"): cur["vo"] = ", ".join(v_old)
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
