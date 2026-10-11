import pytest
from scripts.updater import _is_newer, get_local_version


def test_version_comparison():
    assert _is_newer("1.1.0", "1.0.0") is True
    assert _is_newer("2.0.0", "1.9.9") is True
    assert _is_newer("1.0.1", "1.0.0") is True
    assert _is_newer("1.0.0", "1.0.0") is False
    assert _is_newer("1.0.0", "1.1.0") is False


def test_get_local_version():
    ver = get_local_version()
    assert isinstance(ver, str)
    assert len(ver.split(".")) >= 2
