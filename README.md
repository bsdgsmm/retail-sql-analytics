# Retail SQL Analytics

A practical SQL analytics project exploring retail sales, revenue trends, product performance, customer purchasing patterns, and business KPIs.

The project models a small multi-category retailer and analyzes its transactions with [DuckDB](https://duckdb.org/), a free, open-source, in-process SQL engine.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The database schema is defined in [`sql/00_schema.sql`](sql/00_schema.sql).

## Sample Data

> The dataset is synthetic. All customers, products, and transactions are fictional.

The CSV files in [`data/sample/`](data/sample) are produced by a deterministic generator with a fixed seed (`42`):

```bash
python scripts/generate_sample_data.py
python -m pytest tests/test_data.py
```

## Running the SQL Queries

```bash
python scripts/run_queries.py                                   # all analysis files
python scripts/run_queries.py sql/01_basic_queries.sql          # a single file
```

| File | Concepts |
| --- | --- |
| [`01_basic_queries.sql`](sql/01_basic_queries.sql) | `SELECT`, `WHERE`, `ORDER BY`, `GROUP BY`, `HAVING`, aggregates, `CASE`, `COALESCE`, `NULLIF`, `FILTER` |
| [`02_joins_and_aggregations.sql`](sql/02_joins_and_aggregations.sql) | `INNER JOIN`, `LEFT JOIN`, anti-joins, multi-table joins, conditional aggregation |
| [`03_ctes_and_subqueries.sql`](sql/03_ctes_and_subqueries.sql) | CTEs, chained CTEs, scalar and correlated subqueries, `EXISTS`/`NOT EXISTS`, cohorts, recursive CTE |
| [`04_window_functions.sql`](sql/04_window_functions.sql) | `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`, running totals, moving averages, percent of total |
