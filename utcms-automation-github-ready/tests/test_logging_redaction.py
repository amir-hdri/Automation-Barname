import logging

from app.core.logging import JsonFormatter, sanitize


def test_sanitize_redacts_sensitive_dict_keys():
    data = {"api_key": "abc", "password": "secret", "nested": {"token": "value"}}
    cleaned = sanitize(data)

    assert cleaned["api_key"] == "***"
    assert cleaned["password"] == "***"
    assert cleaned["nested"]["token"] == "***"


def test_json_formatter_includes_request_id_and_redacted_message():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="api_key=SECRET123",
        args=(),
        exc_info=None,
    )
    record.request_id = "rid-1"

    payload = formatter.format(record)
    assert "rid-1" in payload
    assert "SECRET123" not in payload
