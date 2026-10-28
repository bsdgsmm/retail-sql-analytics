import csv
import subprocess
import sys
from collections import defaultdict
from decimal import Decimal

import pytest

from scripts.database import PROJECT_ROOT, SAMPLE_DATA_DIR, SQL_DIR, read_statements

CENT = Decimal("0.01")
TOLERANCE = Decimal("0.01")


def read_table(table):
    with (SAMPLE_DATA_DIR / f"{table}.csv").open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def run_query(connection, file_name, query_number):
    statement = read_statements(SQL_DIR / file_name)[query_number - 1]
    cursor = connection.execute(statement)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def money(value):
    return Decimal(str(value)).quantize(CENT)


@pytest.fixture(scope="module")
def reference():
    orders = {int(row["order_id"]): row for row in read_table("orders")}
    products = {int(row["product_id"]): row for row in read_table("products")}
    completed_ids = {order_id for order_id, row in orders.items() if row["status"] == "completed"}

    gross_sales = Decimal(0)
    net_revenue = Decimal(0)
    cost_of_goods = Decimal(0)
    units = 0
    revenue_by_product = defaultdict(Decimal)
    revenue_by_year = defaultdict(Decimal)
    for item in read_table("order_items"):
        order_id = int(item["order_id"])
        if order_id not in completed_ids:
            continue
        quantity = int(item["quantity"])
        line_gross = quantity * Decimal(item["unit_price"])
        line_net = line_gross * (1 - Decimal(item["discount_pct"]))
        gross_sales += line_gross
        net_revenue += line_net
        cost_of_goods += quantity * Decimal(products[int(item["product_id"])]["unit_cost"])
        units += quantity
        revenue_by_product[int(item["product_id"])] += line_net
        revenue_by_year[orders[order_id]["order_date"][:4]] += line_net

    completed_orders_by_customer = defaultdict(int)
    years_by_customer = defaultdict(set)
    for order_id in completed_ids:
        customer_id = int(orders[order_id]["customer_id"])
        completed_orders_by_customer[customer_id] += 1
        years_by_customer[customer_id].add(orders[order_id]["order_date"][:4])

    return {
        "orders": orders,
        "completed_ids": completed_ids,
        "gross_sales": gross_sales,
        "net_revenue": net_revenue,
        "cost_of_goods": cost_of_goods,
        "units": units,
        "revenue_by_product": revenue_by_product,
        "revenue_by_year": revenue_by_year,
        "completed_orders_by_customer": completed_orders_by_customer,
        "years_by_customer": years_by_customer,
    }


@pytest.fixture(scope="module")
def kpis(connection):
    return {row["metric"]: row["value"] for row in run_query(connection, "05_business_analysis.sql", 1)}


def test_kpi_summary_matches_independent_calculation(kpis, reference):
    completed_orders = len(reference["completed_ids"])
    net_revenue = reference["net_revenue"]
    assert kpis["orders_placed"] == len(reference["orders"])
    assert kpis["completed_orders"] == completed_orders
    assert kpis["active_customers"] == len(reference["completed_orders_by_customer"])
    assert kpis["units_sold"] == reference["units"]
    assert kpis["gross_sales"] == money(reference["gross_sales"])
    assert kpis["net_revenue"] == money(net_revenue)
    assert kpis["gross_profit"] == money(net_revenue - reference["cost_of_goods"])
    assert kpis["average_order_value"] == money(net_revenue / completed_orders)


def test_net_revenue_equals_gross_sales_minus_discounts(kpis):
    assert abs(kpis["gross_sales"] - kpis["discounts"] - kpis["net_revenue"]) <= TOLERANCE


def test_monthly_category_and_region_revenue_reconcile_to_total(connection, kpis):
    monthly = run_query(connection, "05_business_analysis.sql", 4)
    categories = run_query(connection, "05_business_analysis.sql", 3)
    regions = run_query(connection, "02_joins_and_aggregations.sql", 5)
    assert len(monthly) == 24
    for rows in (monthly, categories, regions):
        assert abs(sum(row["net_revenue"] for row in rows) - kpis["net_revenue"]) <= len(rows) * TOLERANCE
    assert sum(row["completed_orders"] for row in monthly) == kpis["completed_orders"]


def test_running_totals_end_at_total_revenue(connection, kpis, reference):
    running = run_query(connection, "04_window_functions.sql", 4)
    assert abs(running[-1]["cumulative_revenue"] - kpis["net_revenue"]) <= TOLERANCE
    year_end_rows = [row for row in running if row["month_start"].month == 12]
    for row in year_end_rows:
        expected = reference["revenue_by_year"][str(row["month_start"].year)]
        assert abs(row["year_to_date_revenue"] - expected) <= TOLERANCE


def test_month_over_month_change_uses_previous_month(connection):
    rows = run_query(connection, "04_window_functions.sql", 3)
    assert rows[0]["previous_month_revenue"] is None
    for previous, current in zip(rows, rows[1:]):
        assert current["previous_month_revenue"] == previous["net_revenue"]
        assert abs(current["mom_change"] - (current["net_revenue"] - previous["net_revenue"])) <= TOLERANCE
    for earlier, later in zip(rows, rows[12:]):
        assert later["same_month_last_year"] == earlier["net_revenue"]


def test_year_over_year_comparison_matches_reference(connection, reference):
    comparison = {row["metric"]: row for row in run_query(connection, "05_business_analysis.sql", 9)}
    revenue = comparison["net_revenue"]
    assert revenue["value_2024"] == money(reference["revenue_by_year"]["2024"])
    assert revenue["value_2025"] == money(reference["revenue_by_year"]["2025"])


def test_top_product_matches_reference(connection, reference):
    products = {int(row["product_id"]): row["product_name"] for row in read_table("products")}
    top_product_id = max(reference["revenue_by_product"], key=reference["revenue_by_product"].get)
    top_row = run_query(connection, "05_business_analysis.sql", 2)[0]
    assert top_row["product_name"] == products[top_product_id]
    assert top_row["net_revenue"] == money(reference["revenue_by_product"][top_product_id])


def test_repeat_customer_rate_matches_reference(connection, reference):
    row = run_query(connection, "05_business_analysis.sql", 6)[0]
    order_counts = reference["completed_orders_by_customer"].values()
    repeat_customers = sum(1 for count in order_counts if count >= 2)
    assert row["purchasing_customers"] == len(order_counts)
    assert row["repeat_customers"] == repeat_customers
    assert row["one_time_customers"] + row["repeat_customers"] == row["purchasing_customers"]
    assert row["repeat_customer_rate_pct"] == round(repeat_customers * 100 / len(order_counts), 1)


def test_retention_matches_reference(connection, reference):
    row = run_query(connection, "05_business_analysis.sql", 7)[0]
    years = reference["years_by_customer"].values()
    assert row["customers_2024"] == sum(1 for active in years if "2024" in active)
    assert row["retained_in_2025"] == sum(1 for active in years if {"2024", "2025"} <= active)
    assert row["new_customers_2025"] == sum(1 for active in years if active == {"2025"})


def test_revenue_concentration_matches_reference(connection, reference):
    row = run_query(connection, "05_business_analysis.sql", 8)[0]
    revenues = sorted(reference["revenue_by_product"].values(), reverse=True)
    total = sum(revenues)
    running = Decimal(0)
    for rank, revenue in enumerate(revenues, start=1):
        running += revenue
        if running / total >= Decimal("0.8"):
            break
    assert row["products_sold"] == len(revenues)
    assert row["products_for_80_pct_revenue"] == rank


def test_status_value_shares_sum_to_one_hundred(connection):
    rows = run_query(connection, "05_business_analysis.sql", 12)
    assert {row["status"] for row in rows} == {"completed", "cancelled", "returned"}
    assert abs(sum(row["share_of_placed_value_pct"] for row in rows) - 100) <= 0.2


def test_top_three_products_per_category(connection):
    rows = run_query(connection, "04_window_functions.sql", 1)
    ranks_by_category = defaultdict(list)
    for row in rows:
        ranks_by_category[row["category_name"]].append(row["rank_in_category"])
    assert len(ranks_by_category) == 8
    assert all(ranks == [1, 2, 3] for ranks in ranks_by_category.values())


def test_spend_quartiles_cover_every_purchasing_customer(connection, kpis):
    rows = run_query(connection, "04_window_functions.sql", 5)
    assert [row["spend_quartile"] for row in rows] == [1, 2, 3, 4]
    assert sum(row["customers"] for row in rows) == kpis["active_customers"]
    assert abs(sum(row["quartile_revenue"] for row in rows) - kpis["net_revenue"]) <= 4 * TOLERANCE


def test_lapsed_customers_have_no_2025_purchases(connection, reference):
    rows = run_query(connection, "03_ctes_and_subqueries.sql", 4)
    expected = {
        customer_id for customer_id, years in reference["years_by_customer"].items() if years == {"2024"}
    }
    assert {row["customer_id"] for row in rows} == expected


def test_customers_without_orders_match_reference(connection, reference):
    rows = run_query(connection, "02_joins_and_aggregations.sql", 3)
    ordering_customers = {int(row["customer_id"]) for row in reference["orders"].values()}
    all_customers = {int(row["customer_id"]) for row in read_table("customers")}
    assert {row["customer_id"] for row in rows} == all_customers - ordering_customers


def test_recursive_calendar_fills_months_without_sales(connection):
    rows = run_query(connection, "03_ctes_and_subqueries.sql", 7)
    assert len(rows) == 24
    assert all(row["units_sold"] == 0 for row in rows if row["month_start"].year == 2024)


def test_query_runner_cli_succeeds():
    result = subprocess.run(
        [sys.executable, "scripts/run_queries.py", "--max-rows", "1"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "05_business_analysis.sql | query 12" in result.stdout


def test_query_runner_rejects_missing_file():
    result = subprocess.run(
        [sys.executable, "scripts/run_queries.py", "sql/missing.sql"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "SQL file not found" in result.stderr


def test_generator_cli_writes_all_tables(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/generate_sample_data.py", "--output-dir", str(tmp_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in tmp_path.glob("*.csv")) == [
        "categories.csv",
        "customers.csv",
        "order_items.csv",
        "orders.csv",
        "products.csv",
    ]
