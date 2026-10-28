from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample"
SCHEMA_FILE = SQL_DIR / "00_schema.sql"
TABLES_IN_LOAD_ORDER = ("categories", "products", "customers", "orders", "order_items")


class DataLoadError(RuntimeError):
    pass


def read_statements(sql_file: Path) -> list[str]:
    sql_text = Path(sql_file).read_text(encoding="utf-8")
    return [statement.query for statement in duckdb.extract_statements(sql_text)]


def analysis_files() -> list[Path]:
    return sorted(path for path in SQL_DIR.glob("*.sql") if path != SCHEMA_FILE)


def create_schema(connection: duckdb.DuckDBPyConnection) -> None:
    for statement in read_statements(SCHEMA_FILE):
        connection.execute(statement)


def load_sample_data(connection: duckdb.DuckDBPyConnection, data_dir: Path = SAMPLE_DATA_DIR) -> None:
    for table in TABLES_IN_LOAD_ORDER:
        csv_path = Path(data_dir) / f"{table}.csv"
        if not csv_path.is_file():
            raise DataLoadError(f"Missing data file: {csv_path}. Run scripts/generate_sample_data.py first.")
        escaped_path = csv_path.as_posix().replace("'", "''")
        try:
            connection.execute(f"COPY {table} FROM '{escaped_path}' (HEADER, NULLSTR '')")
        except duckdb.Error as error:
            raise DataLoadError(f"Could not load {csv_path.name}: {error}") from error


def connect(database: str = ":memory:", data_dir: Path = SAMPLE_DATA_DIR) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(database)
    try:
        create_schema(connection)
        load_sample_data(connection, data_dir)
    except Exception:
        connection.close()
        raise
    return connection
