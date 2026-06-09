import os
from pathlib import Path

from dotenv import load_dotenv

from utils import constants

def get_environment_path():
    filename = ".env.dev" if os.getenv("APP_ENV", "").lower() == "dev" else ".env"
    return constants.BASE_DIR / filename

load_dotenv(get_environment_path())

def load_config():
    required_keys = ["DATABASE_URL", "DATABASE_POOL_MAX"]
    if get_ssl_mode() in constants.CERTIFICATE_SSL_MODES:
        required_keys.append("DATABASE_CA_CERT_PATH")

    missing_keys = [key for key in required_keys if not os.getenv(key)]
    if missing_keys:
        raise RuntimeError(
            f"Missing required database environment variables: {', '.join(missing_keys)}"
        )
    get_database_pool_max()

def get_database_ca_cert_path():
    ca_cert_path = os.getenv("DATABASE_CA_CERT_PATH")
    if ca_cert_path and not Path(ca_cert_path).is_absolute():
        return str(constants.BASE_DIR / ca_cert_path)
    return ca_cert_path

def get_ssl_mode():
    ssl_mode = os.getenv("SSL_MODE", constants.DEFAULT_SSL_MODE).lower()
    if ssl_mode not in constants.POSTGRES_SSL_MODES:
        allowed_modes = ", ".join(sorted(constants.POSTGRES_SSL_MODES))
        raise RuntimeError(f"SSL_MODE must be one of: {allowed_modes}")
    return ssl_mode

def get_leetcode_batch_size():
    return int(
        os.getenv(
            "LEETCODE_BATCH_SIZE",
            str(constants.DEFAULT_LEETCODE_BATCH_SIZE),
        )
    )

def get_leetcode_request_timeout_seconds():
    return int(
        os.getenv(
            "LEETCODE_REQUEST_TIMEOUT_SECONDS",
            str(constants.DEFAULT_LEETCODE_REQUEST_TIMEOUT_SECONDS),
        )
    )

def get_database_pool_max():
    try:
        pool_max = int(os.getenv("DATABASE_POOL_MAX", ""))
    except ValueError as error:
        raise RuntimeError("DATABASE_POOL_MAX must be a positive integer") from error

    if pool_max < 1:
        raise RuntimeError("DATABASE_POOL_MAX must be a positive integer")

    return pool_max
