import pytest

from scripts.database import analysis_files, read_statements

QUERY_CASES = [
    pytest.param(sql_file, index, statement, id=f"{sql_file.stem}-q{index}")
    for sql_file in analysis_files()
    for index, statement in enumerate(read_statements(sql_file), start=1)
]


def test_analysis_files_exist():
    assert analysis_files()


@pytest.mark.parametrize(("sql_file", "index", "statement"), QUERY_CASES)
def test_query_runs_and_returns_rows(connection, sql_file, index, statement):
    rows = connection.execute(statement).fetchall()
    assert rows, f"{sql_file.name} query {index} returned no rows"
