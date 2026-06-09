import json
from urllib.request import Request, urlopen

from utils import constants, load_env


def fetch_graphql_payload(query, variables):
    body = json.dumps(
        {
            "query": query,
            "variables": variables,
        }
    ).encode("utf-8")
    request = Request(
        constants.GRAPHQL_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "leetcode-question-list-crawler",
        },
    )

    with urlopen(
        request,
        timeout=load_env.get_leetcode_request_timeout_seconds(),
    ) as response:
        payload = json.load(response)

    if "errors" in payload:
        raise RuntimeError(f"LeetCode returned GraphQL errors: {payload['errors']}")

    try:
        return payload["data"]
    except KeyError as error:
        raise RuntimeError("LeetCode returned an unexpected GraphQL response") from error


def fetch_question_batch(skip):
    payload = fetch_graphql_payload(
        constants.QUESTION_LIST_QUERY,
        {
            "categorySlug": "",
            "limit": load_env.get_leetcode_batch_size(),
            "skip": skip,
        },
    )
    return payload["problemsetQuestionList"]


def fetch_question_topics(title):
    payload = fetch_graphql_payload(
        constants.QUESTION_DETAIL_QUERY,
        {"titleSlug": title},
    )
    question = payload.get("question")
    if not question:
        return []
    return [topic["name"] for topic in question.get("topicTags", [])]


def format_question(question):
    return {
        "name": question["title"],
        "question_number": int(question["questionFrontendId"]),
        "topics": [topic["name"] for topic in question["topicTags"]],
        "difficulty": question["difficulty"],
        "url": f"https://leetcode.com/problems/{question['titleSlug']}/",
        "premium_required": question["isPaidOnly"],
    }
