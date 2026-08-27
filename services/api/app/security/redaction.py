def redact_secret(value: str | None) -> str | None:
    if not value:
        return value
    return "***redacted***"
