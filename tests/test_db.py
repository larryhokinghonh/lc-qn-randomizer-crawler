from tests.helpers import FakeConnection
from utils import constants, db


def test_get_latest_question_number_reads_database_before_fetching():
    connection = FakeConnection(latest_question_number=3935)

    assert db.get_latest_question_number(connection) == 3935
    assert "MAX(question_number)" in connection.executed[0][0]


def test_insert_questions_skips_database_writes_when_empty():
    connection = FakeConnection()

    assert db.insert_questions(connection, []) == 0
    assert connection.executed == []


def test_insert_questions_writes_questions_topics_and_join_rows():
    connection = FakeConnection()
    questions = [
        {
            "question_number": 3936,
            "name": "Question",
            "topics": ["Array", "Hash Table"],
            "difficulty": "Medium",
            "url": "https://leetcode.com/problems/question/",
            "premium_required": True,
        },
        {
            "question_number": 3937,
            "name": "Another Question",
            "topics": ["Array", "String"],
            "difficulty": "Easy",
            "url": "https://leetcode.com/problems/another-question/",
            "premium_required": False,
        },
    ]

    assert db.insert_questions(connection, questions) == 2

    executed_sql = "\n".join(query for query, _ in connection.executed)
    assert "INSERT INTO leetcode_questions" in executed_sql
    assert "INSERT INTO topics" in executed_sql
    assert "INSERT INTO leetcode_question_topics" in executed_sql
    assert "ON CONFLICT (question_number) DO UPDATE" in executed_sql
    assert "IS DISTINCT FROM" in executed_sql
    assert len(connection.executed) == 5


def test_get_questions_without_topics_returns_titles_from_urls():
    connection = FakeConnection(
        no_topic_rows=[
            (101, 3936, "https://leetcode.com/problems/new-question/"),
            (102, 3937, "https://leetcode.com/problems/another-question"),
        ]
    )

    questions = db.get_questions_without_topics(connection)

    assert questions == [
        {"question_id": 101, "question_number": 3936, "title": "new-question"},
        {"question_id": 102, "question_number": 3937, "title": "another-question"},
    ]


def test_get_database_pool_uses_database_url_ca_cert_and_pool_max(monkeypatch):
    created_pools = []

    class FakePool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.opened = False
            created_pools.append(self)

        def open(self):
            self.opened = True

    monkeypatch.setattr(db, "_database_pool", None)
    monkeypatch.setattr(db, "ConnectionPool", FakePool)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@example.com:5432/database",
    )
    monkeypatch.setenv("DATABASE_CA_CERT_PATH", "certs/root.pem")
    monkeypatch.setenv("DATABASE_POOL_MAX", "3")
    monkeypatch.setenv("SSL_MODE", "verify-full")

    pool = db.get_database_pool()

    assert pool.opened is True
    assert created_pools[0].kwargs == {
        "conninfo": "postgresql://user:password@example.com:5432/database",
        "kwargs": {
            "sslmode": "verify-full",
            "sslrootcert": str(constants.BASE_DIR / "certs/root.pem"),
        },
        "min_size": 0,
        "max_size": 3,
        "open": False,
    }


def test_get_database_pool_disables_ssl_without_ca_certificate(monkeypatch):
    created_pools = []

    class FakePool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.opened = False
            created_pools.append(self)

        def open(self):
            self.opened = True

    monkeypatch.setattr(db, "_database_pool", None)
    monkeypatch.setattr(db, "ConnectionPool", FakePool)
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/database")
    monkeypatch.setenv("DATABASE_POOL_MAX", "1")
    monkeypatch.setenv("SSL_MODE", "disable")
    monkeypatch.delenv("DATABASE_CA_CERT_PATH", raising=False)

    pool = db.get_database_pool()

    assert pool.opened is True
    assert created_pools[0].kwargs == {
        "conninfo": "postgresql://localhost:5432/database",
        "kwargs": {"sslmode": "disable"},
        "min_size": 0,
        "max_size": 1,
        "open": False,
    }
