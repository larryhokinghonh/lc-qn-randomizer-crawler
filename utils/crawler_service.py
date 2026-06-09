import logging
import time

from utils import constants, db, leetcode_client, load_env


logger = logging.getLogger(__name__)


def crawl_new_questions(latest_question_number):
    questions = []
    total_questions = None
    skip = latest_question_number

    while total_questions is None or skip < total_questions:
        result = leetcode_client.fetch_question_batch(skip)
        total_questions = result["totalNum"]
        batch = result["data"]

        logger.info(
            "Fetched LeetCode question batch",
            extra={
                "event": "leetcode_batch_fetched",
                "skip": skip,
                "batch_size": len(batch),
                "total_questions": total_questions,
            },
        )

        if not batch:
            break

        for question in batch:
            formatted_question = leetcode_client.format_question(question)
            if formatted_question["question_number"] > latest_question_number:
                questions.append(formatted_question)

        skip += len(batch)

    return questions


def log_missing_topic_results(results):
    if not results:
        logger.info(
            "Missing-topic scan completed",
            extra={
                "event": "missing_topics_scan_completed",
                "candidate_count": 0,
            },
        )
        return

    candidate_count = len(results)
    total_batches = (
        candidate_count + constants.MISSING_TOPICS_LOG_BATCH_SIZE - 1
    ) // constants.MISSING_TOPICS_LOG_BATCH_SIZE

    for batch_index in range(total_batches):
        start = batch_index * constants.MISSING_TOPICS_LOG_BATCH_SIZE
        batch = results[start : start + constants.MISSING_TOPICS_LOG_BATCH_SIZE]
        updated_count = sum(bool(question["topics"]) for question in batch)
        logger.info(
            "Processed missing-topic question batch",
            extra={
                "event": "missing_topics_batch_processed",
                "batch_number": batch_index + 1,
                "total_batches": total_batches,
                "candidate_count": candidate_count,
                "batch_question_count": len(batch),
                "batch_updated_count": updated_count,
                "batch_unresolved_count": len(batch) - updated_count,
                "questions": [
                    {
                        "question_number": question["question_number"],
                        "title": question["title"],
                        "topics": question["topics"],
                    }
                    for question in batch
                ],
            },
        )


def update_missing_topics(connection):
    questions_without_topics = db.get_questions_without_topics(connection)
    updated_count = 0

    if not questions_without_topics:
        log_missing_topic_results([])
        return updated_count

    topic_updates = []
    topic_results = []
    for question in questions_without_topics:
        topics = leetcode_client.fetch_question_topics(question["title"])
        topic_results.append({**question, "topics": topics})

        if topics:
            topic_updates.append({**question, "topics": topics})

    log_missing_topic_results(topic_results)

    if not topic_updates:
        return updated_count

    with connection.transaction():
        with connection.cursor() as cursor:
            db.add_topics_to_questions(
                cursor,
                {
                    question["question_id"]: question["topics"]
                    for question in topic_updates
                },
            )
            updated_count = len(topic_updates)

    return updated_count


def run_crawler():
    start_time = time.monotonic()
    load_env.load_config()

    with db.connect_to_database() as connection:
        latest_question_number = db.get_latest_question_number(connection)
        logger.info(
            "Read latest question number from PostgreSQL",
            extra={
                "event": "latest_question_number_loaded",
                "latest_question_number": latest_question_number,
            },
        )

        questions = crawl_new_questions(latest_question_number)
        inserted_count = db.insert_questions(connection, questions)
        topics_updated_count = update_missing_topics(connection)

    duration_ms = round((time.monotonic() - start_time) * 1000)
    result = {
        "latest_question_number": latest_question_number,
        "fetched_count": len(questions),
        "inserted_count": inserted_count,
        "topics_updated_count": topics_updated_count,
        "duration_ms": duration_ms,
    }
    logger.info("Crawler run completed", extra={"event": "crawler_completed", **result})
    return result
