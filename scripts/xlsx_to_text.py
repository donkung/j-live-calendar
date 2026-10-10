"""Convert the downloaded workbook into the plain "## Sheet name" + CSV text that parse.py reads."""
import csv, io, sys
import openpyxl

def cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):  # an artist literally named "TRUE"
        return "TRUE" if v else "FALSE"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)

LINK = " <<{}>>"  # parse.py splits "Event name <<https://...>>" back into title + link

def cell_text(c):
    s = cell(c.value)
    target = c.hyperlink.target if c.hyperlink is not None else None
    if s and target and target.startswith("http") and not s.strip().startswith("http"):
        s += LINK.format(target.strip())
    return s

# not read_only: cell hyperlinks are only available in the full loader
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
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
