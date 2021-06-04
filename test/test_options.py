import pytest

from src.options import validate_ttl


def test_validate_ttl():
    # Wrong unit order
    with pytest.raises(ValueError):
        validate_ttl("10d10y")

    # Inexisting unit
    with pytest.raises(ValueError):
        validate_ttl("15x")

    # More than 1 unit
    with pytest.raises(ValueError):
        validate_ttl("1h30m")

    # Valid values
    validate_ttl("10h")
    validate_ttl("5d")
