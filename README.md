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
