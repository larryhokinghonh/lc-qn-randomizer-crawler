import os

from psycopg_pool import ConnectionPool

from utils import load_env


_database_pool = None


def get_database_pool():
    global _database_pool
    if _database_pool is None:
        ssl_mode = load_env.get_ssl_mode()
        connection_kwargs = {"sslmode": ssl_mode}
        ca_cert_path = load_env.get_database_ca_cert_path()
        if ca_cert_path:
            connection_kwargs["sslrootcert"] = ca_cert_path

        _database_pool = ConnectionPool(
            conninfo=os.getenv("DATABASE_URL"),
            kwargs=connection_kwargs,
            min_size=0,
            max_size=load_env.get_database_pool_max(),
            open=False,
        )
        _database_pool.open()

    return _database_pool


def connect_to_database():
    return get_database_pool().connection()


def get_latest_question_number(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(question_number), 0) FROM leetcode_questions")
        return cursor.fetchone()[0]


def extract_title(url):
    return url.rstrip("/").split("/")[-1]


def get_questions_without_topics(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, question_number, url
            FROM leetcode_questions
            WHERE NOT EXISTS (
              SELECT 1
              FROM leetcode_question_topics
              WHERE leetcode_question_topics.question_id = leetcode_questions.id
            )
            ORDER BY question_number
            """
        )
        return [
            {
                "question_id": row[0],
                "question_number": row[1],
                "title": extract_title(row[2]),
            }
            for row in cursor.fetchall()
        ]


def add_topics_to_questions(cursor, topics_by_question_id):
    topic_names = sorted(
        {topic for topics in topics_by_question_id.values() for topic in topics}
    )
    if not topic_names:
        return

    cursor.execute(
        """
        INSERT INTO topics (name)
        SELECT topic_name
        FROM UNNEST(%s::text[]) AS topic_values(topic_name)
        ON CONFLICT (name) DO NOTHING
        """,
        (topic_names,),
    )
    cursor.execute(
        """
        SELECT id, name
        FROM topics
        WHERE name = ANY(%s::text[])
        """,
        (topic_names,),
    )
    topic_ids_by_name = {name: topic_id for topic_id, name in cursor.fetchall()}

    relationships = sorted(
        {
            (question_id, topic_ids_by_name[topic])
            for question_id, topics in topics_by_question_id.items()
            for topic in topics
        }
    )
    cursor.execute(
        """
        INSERT INTO leetcode_question_topics (question_id, topic_id)
        SELECT question_id, topic_id
        FROM UNNEST(%s::bigint[], %s::bigint[])
          AS relationship_values(question_id, topic_id)
        ON CONFLICT (question_id, topic_id) DO NOTHING
        """,
        (
            [question_id for question_id, _ in relationships],
            [topic_id for _, topic_id in relationships],
        ),
    )


def insert_questions(connection, questions):
    if not questions:
        return 0

    with connection.transaction():
        with connection.cursor() as cursor:
            question_numbers = [question["question_number"] for question in questions]
            cursor.execute(
                """
                INSERT INTO leetcode_questions AS existing (
                  question_number,
                  name,
                  difficulty,
                  url,
                  premium_required
                )
                SELECT *
                FROM UNNEST(
                  %s::integer[],
                  %s::text[],
                  %s::text[],
                  %s::text[],
                  %s::boolean[]
                )
                ON CONFLICT (question_number) DO UPDATE SET
                  name = EXCLUDED.name,
                  difficulty = EXCLUDED.difficulty,
                  url = EXCLUDED.url,
                  premium_required = EXCLUDED.premium_required,
                  updated_at = NOW()
                WHERE (
                  existing.name,
                  existing.difficulty,
                  existing.url,
                  existing.premium_required
                ) IS DISTINCT FROM (
                  EXCLUDED.name,
                  EXCLUDED.difficulty,
                  EXCLUDED.url,
                  EXCLUDED.premium_required
                )
                """,
                (
                    question_numbers,
                    [question["name"] for question in questions],
                    [question["difficulty"] for question in questions],
                    [question["url"] for question in questions],
                    [question["premium_required"] for question in questions],
                ),
            )
            cursor.execute(
                """
                SELECT id, question_number
                FROM leetcode_questions
                WHERE question_number = ANY(%s::integer[])
                """,
                (question_numbers,),
            )
            question_ids_by_number = {
                question_number: question_id
                for question_id, question_number in cursor.fetchall()
            }
            add_topics_to_questions(
                cursor,
                {
                    question_ids_by_number[question["question_number"]]: question["topics"]
                    for question in questions
                },
            )

    return len(questions)
