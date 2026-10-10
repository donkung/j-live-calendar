# J-Live Thailand Calendar

A calendar view of Japanese artist concerts and events in Thailand, built from the
[J-con in Thai sheet by strobolights](https://docs.google.com/spreadsheets/d/1EShN2E7TZHCI6U5oS2CKByYXTUDIHZJnJwodrgWvN3k/).
All listings are their work; this repo only re-displays them.

## How it updates

A GitHub Action (`.github/workflows/build.yml`) runs every day at 06:17 Bangkok time, and on every push:

1. downloads the public sheet as `.xlsx`
2. `scripts/xlsx_to_text.py` turns every year tab into CSV text
3. `scripts/parse.py` turns the rows into events (dates, artists, venue, promoter, links)
4. `scripts/build.py` injects them into `template.html` and publishes `site/` to GitHub Pages

To refresh right away: **Actions → Rebuild calendar from sheet → Run workflow**.

If the parse returns fewer than 100 events (for example, the sheet layout changed),
the build fails and the last good version stays online.

## Run locally

```sh
pip install openpyxl
curl -L -o sheet.xlsx "https://docs.google.com/spreadsheets/d/1EShN2E7TZHCI6U5oS2CKByYXTUDIHZJnJwodrgWvN3k/export?format=xlsx"
python scripts/xlsx_to_text.py sheet.xlsx > data.txt
python scripts/parse.py data.txt > events.json
python scripts/build.py events.json
open site/index.html
```
