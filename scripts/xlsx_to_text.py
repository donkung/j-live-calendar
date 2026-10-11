"""Convert the downloaded workbook into the plain "## Sheet name" + CSV text that parse.py reads."""
import csv, io, sys
import openpyxl
from openpyxl.cell.rich_text import CellRichText

def cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):  # an artist literally named "TRUE"
        return "TRUE" if v else "FALSE"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)

LINK = " <<{}>>"  # parse.py splits "Event name <<https://...>>" back into title + link

# Markers read back by parse.py:
#   ~~text~~   struck-through text (whole cell, or one run inside a cell, e.g. an old venue)
#   [[red]]    cell has a red background (the sheet's "cancelled" highlight)
RED_FILL = "FFFF0000"

def is_red_fill(c):
    try:
        f = c.fill
        return bool(f and f.fill_type and f.fgColor is not None and f.fgColor.type == "rgb" and f.fgColor.rgb == RED_FILL)
    except Exception:
        return False

def struck(text):
    core = text.strip()
    return text.replace(core, f"~~{core}~~") if core else text

def cell_text(c):
    v = c.value
    if isinstance(v, CellRichText):
        # plain runs follow the visible text; only runs with their own strike are marked
        s = "".join(r if isinstance(r, str) else (struck(r.text) if r.font is not None and r.font.strike else r.text) for r in v)
    else:
        s = cell(v)
        if s.strip() and c.font is not None and c.font.strike:
            s = struck(s)
    target = c.hyperlink.target if c.hyperlink is not None else None
    if s and target and target.startswith("http") and not s.strip().startswith("http"):
        s += LINK.format(target.strip())
    if s.strip() and is_red_fill(c):
        s += " [[red]]"
    return s

# not read_only: cell hyperlinks are only available in the full loader
wb = openpyxl.load_workbook(sys.argv[1], data_only=True, rich_text=True)
out = io.StringIO()
for ws in wb.worksheets:
    out.write(f"## Sheet name: {ws.title}\n")
    w = csv.writer(out, lineterminator="\n")
    for row in ws.iter_rows():
        r = [cell_text(c) for c in row]
        while r and r[-1] == "":
            r.pop()
        if r:
            w.writerow(r)
    out.write("\n")
sys.stdout.write(out.getvalue())
