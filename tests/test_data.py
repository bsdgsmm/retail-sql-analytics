import csv

import pytest

from scripts.database import SAMPLE_DATA_DIR, TABLES_IN_LOAD_ORDER
from scripts.generate_sample_data import DEFAULT_SEED, write_dataset


def read_csv_rows(path):
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.reader(csv_file))


@pytest.mark.parametrize("table", TABLES_IN_LOAD_ORDER)
def test_committed_sample_matches_generator(tmp_path, table):
    write_dataset(tmp_path, DEFAULT_SEED)
    assert read_csv_rows(tmp_path / f"{table}.csv") == read_csv_rows(SAMPLE_DATA_DIR / f"{table}.csv")


def test_generator_is_seed_dependent(tmp_path):
    write_dataset(tmp_path, DEFAULT_SEED + 1)
    assert read_csv_rows(tmp_path / "orders.csv") != read_csv_rows(SAMPLE_DATA_DIR / "orders.csv")


@pytest.mark.parametrize(
    ("table", "minimum_rows"),
    [("categories", 8), ("products", 60), ("customers", 500), ("orders", 4000), ("order_items", 8000)],
)
def test_tables_are_populated(connection, table, minimum_rows):
    assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] >= minimum_rows


@pytest.mark.parametrize(
    ("child_table", "child_key", "parent_table", "parent_key"),
    [
        ("products", "category_id", "categories", "category_id"),
        ("orders", "customer_id", "customers", "customer_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
    ],
)
def test_foreign_keys_resolve(connection, child_table, child_key, parent_table, parent_key):
    orphan_count = connection.execute(
        f"""
        SELECT count(*)
        FROM {child_table} AS child
        LEFT JOIN {parent_table} AS parent ON child.{child_key} = parent.{parent_key}
        WHERE parent.{parent_key} IS NULL
        """
    ).fetchone()[0]
    assert orphan_count == 0


def test_every_order_has_items(connection):
    empty_orders = connection.execute(
        "SELECT count(*) FROM orders WHERE order_id NOT IN (SELECT order_id FROM order_items)"
    ).fetchone()[0]
    assert empty_orders == 0


def test_orders_follow_customer_signup_and_product_launch(connection):
    violations = connection.execute(
        """
        SELECT count(*)
        FROM orders AS o
        JOIN customers AS c USING (customer_id)
        JOIN order_items AS oi USING (order_id)
        JOIN products AS p USING (product_id)
        WHERE o.order_date < c.signup_date OR o.order_date < p.launch_date
        """
    ).fetchone()[0]
    assert violations == 0


def test_order_dates_cover_two_full_years(connection):
    first_date, last_date, month_count = connection.execute(
        "SELECT min(order_date), max(order_date), count(DISTINCT date_trunc('month', order_date)) FROM orders"
    ).fetchone()
    assert (first_date.isoformat(), last_date.isoformat(), month_count) == ("2024-01-01", "2025-12-31", 24)


def test_discount_is_consistent_within_each_order(connection):
    inconsistent_orders = connection.execute(
        """
        SELECT count(*)
        FROM (
            SELECT order_id
            FROM order_items
            GROUP BY order_id
            HAVING count(DISTINCT discount_pct) > 1
        )
        """
    ).fetchone()[0]
    assert inconsistent_orders == 0


def test_promo_code_and_discount_agree(connection):
    mismatches = connection.execute(
        """
        SELECT count(*)
        FROM orders AS o
        JOIN order_items AS oi USING (order_id)
        WHERE (o.promo_code IS NULL) <> (oi.discount_pct = 0)
        """
    ).fetchone()[0]
    assert mismatches == 0


def test_dataset_contains_cases_for_null_and_outer_join_analysis(connection):
    missing_emails, missing_referrals, customers_without_orders = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE email IS NULL),
            count(*) FILTER (WHERE referral_source IS NULL),
            count(*) FILTER (WHERE customer_id NOT IN (SELECT customer_id FROM orders))
        FROM customers
        """
    ).fetchone()
    assert missing_emails > 0
    assert missing_referrals > 0
    assert customers_without_orders > 0


def test_unit_price_matches_product_list_price(connection):
    mismatches = connection.execute(
        "SELECT count(*) FROM order_items JOIN products USING (product_id) WHERE unit_price <> list_price"
    ).fetchone()[0]
    assert mismatches == 0
