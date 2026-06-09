import json

import pytest

from utils import constants, leetcode_client


def test_fetch_question_topics_reads_detail_graphql_response(monkeypatch):
    def fake_fetch_graphql_payload(query, variables):
        assert query == constants.QUESTION_DETAIL_QUERY
        assert variables == {"titleSlug": "new-question"}
        return {
            "question": {
                "topicTags": [
                    {"name": "Array"},
                    {"name": "Hash Table"},
                ]
            }
        }

    monkeypatch.setattr(
        leetcode_client,
        "fetch_graphql_payload",
        fake_fetch_graphql_payload,
    )

    assert leetcode_client.fetch_question_topics("new-question") == [
        "Array",
        "Hash Table",
    ]


def test_fetch_question_batch_raises_on_graphql_errors(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps({"errors": [{"message": "bad request"}]}).encode(
                "utf-8"
            )

    monkeypatch.setattr(
        leetcode_client,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )

    with pytest.raises(RuntimeError, match="GraphQL errors"):
        leetcode_client.fetch_question_batch(0)
