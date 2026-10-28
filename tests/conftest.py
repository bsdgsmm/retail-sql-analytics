import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.database import connect


@pytest.fixture(scope="session")
def connection():
    database = connect()
    yield database
    database.close()
