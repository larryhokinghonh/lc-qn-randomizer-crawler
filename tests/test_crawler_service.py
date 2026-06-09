import logging

from tests.helpers import FakeConnection, make_leetcode_question
from utils import crawler_service


def test_crawl_new_questions_filters_existing_questions(monkeypatch):
    def fake_fetch(skip):
        assert skip == 2
        return {
            "totalNum": 5,
            "data": [
                make_leetcode_question(2, "Existing"),
                make_leetcode_question(3, "Three"),
                make_leetcode_question(4, "Four"),
            ],
        }

    monkeypatch.setattr(
        crawler_service.leetcode_client,
        "fetch_question_batch",
        fake_fetch,
    )

    questions = crawler_service.crawl_new_questions(2)

    assert [question["question_number"] for question in questions] == [3, 4]


def test_update_missing_topics_fetches_and_writes_topic_joins(monkeypatch):
    connection = FakeConnection(
        no_topic_rows=[(101, 3936, "https://leetcode.com/problems/new-question/")]
    )
    monkeypatch.setattr(
        crawler_service.leetcode_client,
        "fetch_question_topics",
        lambda title: ["Array", "Hash Table"],
    )

    assert crawler_service.update_missing_topics(connection) == 1

    executed_sql = "\n".join(query for query, _ in connection.executed)
    assert "WHERE NOT EXISTS" in executed_sql
    assert "INSERT INTO topics" in executed_sql
    assert "INSERT INTO leetcode_question_topics" in executed_sql
    assert "WHERE question_number = %s" not in executed_sql
    assert len(connection.executed) == 4


def test_update_missing_topics_leaves_questions_without_new_topics_unchanged(
    monkeypatch,
):
    connection = FakeConnection(
        no_topic_rows=[(101, 3936, "https://leetcode.com/problems/new-question/")]
    )
    monkeypatch.setattr(
        crawler_service.leetcode_client,
        "fetch_question_topics",
        lambda title: [],
    )

    assert crawler_service.update_missing_topics(connection) == 0

    executed_sql = "\n".join(query for query, _ in connection.executed)
    assert "WHERE NOT EXISTS" in executed_sql
    assert "INSERT INTO topics" not in executed_sql


def test_update_missing_topics_logs_results_in_batches(monkeypatch, caplog):
    no_topic_rows = [
        (
            question_number,
            question_number,
            f"https://leetcode.com/problems/question-{question_number}/",
        )
        for question_number in range(1, 116)
    ]
    connection = FakeConnection(no_topic_rows=no_topic_rows)
    monkeypatch.setattr(
        crawler_service.leetcode_client,
        "fetch_question_topics",
        lambda title: ["Array"] if title in {"question-1", "question-51"} else [],
    )

    with caplog.at_level(logging.INFO, logger=crawler_service.logger.name):
        assert crawler_service.update_missing_topics(connection) == 2

    batch_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "missing_topics_batch_processed"
    ]
    assert len(batch_records) == 3
    assert [record.batch_question_count for record in batch_records] == [50, 50, 15]
    assert [record.batch_updated_count for record in batch_records] == [1, 1, 0]
    assert [record.batch_unresolved_count for record in batch_records] == [49, 49, 15]
    assert all(record.candidate_count == 115 for record in batch_records)
    assert all(record.total_batches == 3 for record in batch_records)
    assert batch_records[0].questions[0] == {
        "question_number": 1,
        "title": "question-1",
        "topics": ["Array"],
    }
    assert not any(
        getattr(record, "event", None) == "question_topics_fetched"
        for record in caplog.records
    )


def test_update_missing_topics_logs_empty_scan(caplog):
    connection = FakeConnection()

    with caplog.at_level(logging.INFO, logger=crawler_service.logger.name):
        assert crawler_service.update_missing_topics(connection) == 0

    scan_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "missing_topics_scan_completed"
    ]
    assert len(scan_records) == 1
    assert scan_records[0].candidate_count == 0
