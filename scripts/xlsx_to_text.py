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

wb = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)
out = io.StringIO()
for ws in wb.worksheets:
    out.write(f"## Sheet name: {ws.title}\n")
    w = csv.writer(out, lineterminator="\n")
    for row in ws.iter_rows(values_only=True):
        r = [cell(v) for v in row]
        while r and r[-1] == "":
            r.pop()
        if r:
            w.writerow(r)
    out.write("\n")
sys.stdout.write(out.getvalue())
