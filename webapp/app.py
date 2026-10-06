"""Read-only dashboard for the sales analysis.

Serves the SQL analysis results and the matplotlib charts that Sales_Analysis.py
produces, driven by the sales table that webapp/load_data.py loads.
"""
import os

from flask import Flask, Response, abort, render_template

import analysis

app = Flask(__name__)

CHART_NAMES = tuple(analysis.CHARTS)


def money(value):
    return None if value is None else f"${float(value):,.2f}"


def number(value):
    return None if value is None else f"{float(value):,.0f}"


def percent(value):
    return None if value is None else f"{float(value):+.2f}%"


def month(value):
    return None if value is None else str(value)[:7]


def records(frame, formatters=None):
    formatters = formatters or {}
    return [
        {key: formatters.get(key, lambda v: v)(value) for key, value in row.items()}
        for row in frame.to_dict("records")
    ]


@app.route("/")
def index():
    metrics = analysis.summary()
    return render_template(
        "index.html",
        metrics={
            "orders": f"{metrics['orders']:,}",
            "units_sold": f"{metrics['units_sold']:,}",
            "total_revenue": money(metrics["total_revenue"]),
            "avg_order_value": money(metrics["avg_order_value"]),
        },
        region_rows=records(analysis.revenue_by_region(), {"total_revenue": money}),
        product_rows=records(analysis.revenue_by_product(), {"total_revenue": money}),
        monthly_rows=records(
            analysis.monthly_growth(),
            {
                "month": month,
                "total_revenue": money,
                "previous_revenue": money,
                "growth_rate": percent,
            },
        ),
        customer_rows=records(analysis.top_customers(), {"total_revenue": money}),
        outlier_rows=records(
            analysis.price_outliers(),
            {"price_per_unit": money, "order_date": lambda v: str(v)},
        ),
        charts=[name for name in CHART_NAMES],
    )


@app.route("/charts/<name>.png")
def chart(name):
    if name not in analysis.CHARTS:
        abort(404)
    return Response(analysis.CHARTS[name]().read(), mimetype="image/png")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "3000")),
        debug=True,
        use_reloader=True,
    )
