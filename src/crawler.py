import json
import logging

from utils.crawler_service import run_crawler
from utils.log_config import configure_logging


configure_logging()
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        result = run_crawler()
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception:
        logger.exception("Crawler run failed", extra={"event": "crawler_failed"})
        raise


def main():
    print(json.dumps(run_crawler(), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
