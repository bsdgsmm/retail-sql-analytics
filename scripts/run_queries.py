import argparse
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.database import DataLoadError, analysis_files, connect, read_statements


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the sample retail dataset into DuckDB and execute analysis SQL files."
    )
    parser.add_argument(
        "sql_files",
        nargs="*",
        type=Path,
        help="SQL files to execute. Defaults to every analysis file in sql/.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=20,
        help="Maximum number of rows to display per query (default: 20).",
    )
    return parser.parse_args()


def run_file(connection: duckdb.DuckDBPyConnection, sql_file: Path, max_rows: int) -> None:
    for index, statement in enumerate(read_statements(sql_file), start=1):
        print(f"\n=== {sql_file.name} | query {index} ===")
        connection.sql(statement).show(max_rows=max_rows, max_width=200)


def main() -> int:
    arguments = parse_arguments()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sql_files = arguments.sql_files or analysis_files()
    missing_files = [path for path in sql_files if not path.is_file()]
    if missing_files:
        print(f"SQL file not found: {', '.join(map(str, missing_files))}", file=sys.stderr)
        return 1
    try:
        connection = connect()
    except DataLoadError as error:
        print(error, file=sys.stderr)
        return 1
    try:
        for sql_file in sql_files:
            run_file(connection, sql_file, arguments.max_rows)
    except duckdb.Error as error:
        print(f"Query failed: {error}", file=sys.stderr)
        return 1
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
