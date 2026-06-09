from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

POSTGRES_SSL_MODES = {
    "disable",
    "verify-full",
}
CERTIFICATE_SSL_MODES = {"verify-full"}
DEFAULT_SSL_MODE = "verify-full"

DEFAULT_LEETCODE_BATCH_SIZE = 1000
DEFAULT_LEETCODE_REQUEST_TIMEOUT_SECONDS = 30
MISSING_TOPICS_LOG_BATCH_SIZE = 50

GRAPHQL_URL = "https://leetcode.com/graphql/"
QUESTION_LIST_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: {}
  ) {
    totalNum
    data {
      questionFrontendId
      title
      titleSlug
      difficulty
      isPaidOnly
      topicTags {
        name
      }
    }
  }
}
"""
QUESTION_DETAIL_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    topicTags {
      name
    }
  }
}
"""
