import pytest

from utils import constants, load_env


def test_get_environment_path_defaults_to_production_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)

    assert load_env.get_environment_path() == constants.BASE_DIR / ".env"


def test_get_environment_path_uses_development_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")

    assert load_env.get_environment_path() == constants.BASE_DIR / ".env.dev"


def test_get_database_ca_cert_path_resolves_relative_path(monkeypatch):
    monkeypatch.setenv("DATABASE_CA_CERT_PATH", "certs/root.pem")

    assert load_env.get_database_ca_cert_path() == str(
        constants.BASE_DIR / "certs/root.pem"
    )


def test_get_database_pool_max_requires_positive_integer(monkeypatch):
    monkeypatch.setenv("DATABASE_POOL_MAX", "0")

    with pytest.raises(RuntimeError, match="DATABASE_POOL_MAX must be a positive integer"):
        load_env.get_database_pool_max()


def test_get_ssl_mode_defaults_to_verify_full(monkeypatch):
    monkeypatch.delenv("SSL_MODE", raising=False)

    assert load_env.get_ssl_mode() == "verify-full"


def test_get_ssl_mode_rejects_unsupported_mode(monkeypatch):
    monkeypatch.setenv("SSL_MODE", "unsupported")

    with pytest.raises(RuntimeError, match="SSL_MODE must be one of"):
        load_env.get_ssl_mode()


def test_load_config_requires_database_credentials(monkeypatch):
    for key in ["DATABASE_URL", "DATABASE_CA_CERT_PATH", "DATABASE_POOL_MAX"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SSL_MODE", "verify-full")

    with pytest.raises(RuntimeError, match="Missing required database environment variables"):
        load_env.load_config()


def test_load_config_allows_disabled_ssl_without_ca_certificate(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/database")
    monkeypatch.setenv("DATABASE_POOL_MAX", "1")
    monkeypatch.setenv("SSL_MODE", "disable")
    monkeypatch.delenv("DATABASE_CA_CERT_PATH", raising=False)

    load_env.load_config()


def test_load_config_requires_ca_certificate_for_verify_full(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.com/database")
    monkeypatch.setenv("DATABASE_POOL_MAX", "1")
    monkeypatch.setenv("SSL_MODE", "verify-full")
    monkeypatch.delenv("DATABASE_CA_CERT_PATH", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_CA_CERT_PATH"):
        load_env.load_config()
