# LeetCode Question Randomizer Crawler

A Python crawler that updates the database used by LeetCode Question Randomizer. It is designed to run as a scheduled AWS Lambda function deployed with AWS SAM.

The crawler is idempotent. It reads the highest stored question number before fetching new questions. It also revisits database questions without topics, since LeetCode may add topic metadata after publishing a question.

## Prerequisites

- Python 3.12
- PostgreSQL
- AWS CLI and AWS SAM CLI installed
- Docker Desktop

## Local Setup

Create and populate the virtual environment:

```cmd
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

- Configure `.env` and place the database CA certificate at the configured path.

Run the crawler against the SSL-secured database:

```cmd
.\venv\Scripts\python.exe -m src.crawler
```

To use a local development database, copy `.env.dev.template` to `.env.dev`,
provide the local database URL, and run:

```cmd
$env:APP_ENV="dev"
.\venv\Scripts\python.exe -m src.crawler
```

The development file uses `SSL_MODE=disable` and does not require
`DATABASE_CA_CERT_PATH`. Clear `APP_ENV` before returning to `.env`:

```cmd
set APP_ENV=
```

## SAM Build and Deployment

Validate the template:

```cmd
sam validate --lint
```

Build inside the Lambda-compatible Linux container:

```cmd
sam build --use-container
```

The Makefile packages runtime dependencies, `src/crawler.py`, `utils/`, and the CA certificate into `.aws-sam/build/`.

To deploy, use:

```cmd
sam build --use-container
sam deploy
```

To deploy interactively:

```cmd
sam deploy --guided
```

Provide values for `DatabaseUrl` and `AlarmEmail`. Review other parameters such as `ScheduleExpression`, `TimeoutSeconds`, `MemorySize`, `DatabasePoolMax`, and `LogRetentionDays`. After deployment, confirm the SNS email subscription.

## Testing

The tests mock LeetCode and PostgreSQL, so they do not require live services:

```cmd
.\venv\Scripts\python.exe -m pytest -q
```

Compile-check the application modules:

```cmd
.\venv\Scripts\python.exe -m compileall -q src utils
```