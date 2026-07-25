from src.report_formatter import format_report


def test_format_report_healthy():
    out = format_report("api", True)
    assert "name: api" in out
    assert "status: ok" in out


def test_format_report_down():
    out = format_report("api", False)
    assert "status: down" in out
