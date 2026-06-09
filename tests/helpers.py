def make_leetcode_question(number, title="New Question", topics=None):
    return {
        "questionFrontendId": str(number),
        "title": title,
        "titleSlug": title.lower().replace(" ", "-"),
        "difficulty": "Easy",
        "isPaidOnly": False,
        "topicTags": [{"name": topic} for topic in (topics or ["Array"])],
    }


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.last_result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.connection.executed.append((query, params))

        if "MAX(question_number)" in query:
            self.last_result = (self.connection.latest_question_number,)
        elif "WHERE NOT EXISTS" in query:
            self.last_result = self.connection.no_topic_rows
        elif "SELECT id, question_number" in query:
            question_numbers = params[0]
            for question_number in question_numbers:
                if question_number not in self.connection.question_ids_by_number:
                    self.connection.question_ids_by_number[question_number] = (
                        self.connection.next_question_id
                    )
                    self.connection.next_question_id += 1
            self.last_result = [
                (self.connection.question_ids_by_number[number], number)
                for number in question_numbers
            ]
        elif "SELECT id, name" in query and "FROM topics" in query:
            topic_names = params[0]
            for topic_name in topic_names:
                if topic_name not in self.connection.topic_ids_by_name:
                    self.connection.topic_ids_by_name[topic_name] = (
                        self.connection.next_topic_id
                    )
                    self.connection.next_topic_id += 1
            self.last_result = [
                (self.connection.topic_ids_by_name[name], name)
                for name in topic_names
            ]
        else:
            self.last_result = None

    def fetchone(self):
        return self.last_result

    def fetchall(self):
        return self.last_result


class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeConnection:
    def __init__(self, latest_question_number=0, no_topic_rows=None):
        self.latest_question_number = latest_question_number
        self.no_topic_rows = no_topic_rows or []
        self.question_ids_by_number = {
            question_number: question_id
            for question_id, question_number, _url in self.no_topic_rows
        }
        self.topic_ids_by_name = {}
        self.executed = []
        self.next_question_id = 10
        self.next_topic_id = 100

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return FakeCursor(self)

    def transaction(self):
        return FakeTransaction()
