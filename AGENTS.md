# AGENTS.md

Non-obvious notes for working on this repository in the Base44 sandbox.

## What this repo is

A data-analysis project (PostgreSQL + Python/matplotlib), not a web app. Originally it was
run by hand: `Sales_Analysis.py` reads a hardcoded Windows path
(`C:/tmp/sales_project_export.csv`), prints to stdout and calls `plt.show()`, and
`sales_analysis_queries.sql` is meant to be pasted into psql. Neither is wired to a database.

`docker-compose.base44.yml` brings the pipeline up in the sandbox and adds a small read-only
viewer so the analysis is visible in the preview:

- **db** — PostgreSQL 16, data in the `sales_pgdata` volume.
- **loader** — one-shot service (`webapp/load_data.py`) that truncates and loads
  `data/sales_project_export.csv` into a `sales` table. Re-runnable: `docker compose -f
  docker-compose.base44.yml run --rm loader`.
- **web** — Flask dashboard (`webapp/app.py`) on port 3000, rendering the analysis results and
  matplotlib charts generated live from the database (mirrors `Sales_Analysis.py`).

## Details worth knowing

- `data/sales_project_export.csv` (1005 rows, lowercase headers) is the input; its columns match
  the `sales` schema in `sales_analysis_queries.sql`. Dates are `dd/mm/yyyy`.
- The SQL file uses unquoted mixed-case identifiers, which PostgreSQL folds to lowercase, so its
  queries run as-is against the lowercase `sales` table.
- `requirments.txt` (note the typo) lists `psycopg2`, which needs a compiler; the web app uses
  `webapp/requirements.txt` with `psycopg2-binary` instead.
- The README's headline insights (North highest revenue, Smartphones 45%) do **not** match the
  data in `data/sales_project_export.csv` — verify against the database before repeating them.
- `notebooks/Sales_Analysis.ipynb` is referenced in the README but does not exist in the repo.

## Verifying it works

```bash
docker compose -f docker-compose.base44.yml up -d --build
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/          # expect 200
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/charts/region.png  # expect 200
docker compose -f docker-compose.base44.yml exec -T db \
  psql -U sales -d sales -c "select count(*) from sales;"                # expect 1005
```

There are no tests and no lint configuration in this repository.
