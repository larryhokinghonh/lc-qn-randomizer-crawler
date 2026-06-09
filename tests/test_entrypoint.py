import json

from src import crawler


def test_lambda_handler_returns_summary(monkeypatch):
    monkeypatch.setattr(
        crawler,
        "run_crawler",
        lambda: {
            "latest_question_number": 3935,
            "fetched_count": 2,
            "inserted_count": 2,
            "topics_updated_count": 1,
            "duration_ms": 10,
        },
    )

    response = crawler.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["inserted_count"] == 2
