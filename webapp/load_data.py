"""One-shot ETL: load data/sales_project_export.csv into the PostgreSQL `sales` table.

Mirrors the schema used by sales_analysis_queries.sql (Quantity, Price_Per_Unit,
Order_Date, Region, ...) and is safe to re-run: it truncates before loading.
"""
import csv
import os
import sys
import time
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values

CSV_PATH = os.environ.get("SALES_CSV", "data/sales_project_export.csv")

DDL = """
CREATE TABLE IF NOT EXISTS sales (
    order_id       INTEGER PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    product        TEXT NOT NULL,
    quantity       INTEGER NOT NULL,
    price_per_unit NUMERIC(12, 4) NOT NULL,
    order_date     DATE NOT NULL,
    region         TEXT NOT NULL
);
"""

INSERT = """
INSERT INTO sales (order_id, customer_name, product, quantity, price_per_unit, order_date, region)
VALUES %s
"""


def connect():
    dsn = dict(
        host=os.environ.get("PGHOST", "db"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "sales"),
        password=os.environ.get("PGPASSWORD", ""),
        dbname=os.environ.get("PGDATABASE", "sales"),
    )
    last_error = None
    for attempt in range(10):
        try:
            return psycopg2.connect(**dsn)
        except psycopg2.OperationalError as exc:  # database still starting up
            last_error = exc
            time.sleep(2)
    raise SystemExit(f"could not reach PostgreSQL: {last_error}")


def rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            yield (
                int(record["order_id"]),
                record["customer_name"],
                record["product"],
                int(record["quantity"]),
                float(record["price_per_unit"]),
                datetime.strptime(record["order_date"], "%d/%m/%Y").date(),
                record["region"],
            )


def main():
    data = list(rows())
    with connect() as conn, conn.cursor() as cur:
        cur.execute(DDL)
        cur.execute("TRUNCATE sales")
        execute_values(cur, INSERT, data)
    print(f"loaded {len(data)} rows from {CSV_PATH} into sales", flush=True)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        sys.exit(f"missing CSV file: {CSV_PATH}")
