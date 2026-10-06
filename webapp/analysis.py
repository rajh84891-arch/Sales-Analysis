"""Sales analysis: SQL queries against PostgreSQL plus matplotlib charts.

The queries mirror the ones in sales_analysis_queries.sql; the charts mirror the
ones produced by Sales_Analysis.py.
"""
import io
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import psycopg2

DSN = dict(
    host=os.environ.get("PGHOST", "db"),
    port=os.environ.get("PGPORT", "5432"),
    user=os.environ.get("PGUSER", "sales"),
    password=os.environ.get("PGPASSWORD", ""),
    dbname=os.environ.get("PGDATABASE", "sales"),
)

REVENUE = "SUM(quantity * price_per_unit)"


def query(sql):
    with psycopg2.connect(**DSN) as conn, conn.cursor() as cur:
        cur.execute(sql)
        columns = [column.name for column in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


def summary():
    row = query(
        f"""
        SELECT COUNT(*)                     AS orders,
               COALESCE({REVENUE}, 0)       AS total_revenue,
               COALESCE(AVG(quantity * price_per_unit), 0) AS avg_order_value,
               COALESCE(SUM(quantity), 0)   AS units_sold
        FROM sales
        """
    ).iloc[0]
    return {
        "orders": int(row["orders"]),
        "total_revenue": float(row["total_revenue"]),
        "avg_order_value": float(row["avg_order_value"]),
        "units_sold": int(row["units_sold"]),
    }


def revenue_by_region():
    return query(
        f"""
        SELECT region AS region, {REVENUE} AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
        """
    )


def revenue_by_product():
    return query(
        f"""
        SELECT product AS product, {REVENUE} AS total_revenue
        FROM sales
        GROUP BY product
        ORDER BY total_revenue DESC
        """
    )


def monthly_revenue():
    return query(
        f"""
        SELECT DATE_TRUNC('month', order_date) AS month, {REVENUE} AS total_revenue
        FROM sales
        GROUP BY DATE_TRUNC('month', order_date)
        ORDER BY month
        """
    )


def monthly_growth():
    return query(
        f"""
        WITH monthly AS (
            SELECT DATE_TRUNC('month', order_date) AS month, {REVENUE} AS total_revenue
            FROM sales
            GROUP BY DATE_TRUNC('month', order_date)
        )
        SELECT month,
               total_revenue,
               LAG(total_revenue) OVER (ORDER BY month) AS previous_revenue,
               ROUND(
                   (total_revenue - LAG(total_revenue) OVER (ORDER BY month))
                   / LAG(total_revenue) OVER (ORDER BY month) * 100, 2
               ) AS growth_rate
        FROM monthly
        ORDER BY month
        """
    )


def top_customers(limit=10):
    return query(
        f"""
        SELECT customer_name AS customer_name, {REVENUE} AS total_revenue
        FROM sales
        GROUP BY customer_name
        ORDER BY total_revenue DESC
        LIMIT {int(limit)}
        """
    )


def price_outliers(limit=100):
    return query(
        f"""
        SELECT order_id, customer_name, product, quantity, price_per_unit, order_date, region
        FROM sales
        WHERE price_per_unit > 1500 OR price_per_unit < 50
        ORDER BY price_per_unit DESC
        LIMIT {int(limit)}
        """
    )


def _png(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _bar(labels, values, title, color):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(labels, values, color=color)
    ax.set_title(title)
    ax.set_ylabel("Total Revenue")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    return _png(fig)


def chart_region():
    data = revenue_by_region()
    return _bar(data["region"], data["total_revenue"].astype(float),
                "Total Revenue by Region", "skyblue")


def chart_product():
    data = revenue_by_product()
    return _bar(data["product"], data["total_revenue"].astype(float),
                "Total Revenue by Product", "purple")


def chart_customers():
    data = top_customers()
    return _bar(data["customer_name"], data["total_revenue"].astype(float),
                "Top 10 Customers by Total Revenue", "green")


def chart_monthly():
    data = monthly_revenue()
    months = pd.to_datetime(data["month"]).dt.strftime("%Y-%m")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(months, data["total_revenue"].astype(float), marker="o", color="orange")
    ax.set_title("Monthly Revenue Trends")
    ax.set_ylabel("Total Revenue")
    ax.grid(True, linestyle=":", alpha=0.5)
    return _png(fig)


def chart_outliers():
    prices = query("SELECT price_per_unit FROM sales")["price_per_unit"].astype(float)
    fig, ax = plt.subplots(figsize=(9, 2.8))
    ax.boxplot(prices, vert=False, patch_artist=True)
    ax.set_title("Boxplot of Price Per Unit")
    ax.set_xlabel("Price Per Unit")
    return _png(fig)


CHARTS = {
    "region": chart_region,
    "product": chart_product,
    "monthly": chart_monthly,
    "customers": chart_customers,
    "outliers": chart_outliers,
}
