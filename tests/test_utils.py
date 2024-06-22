""" Tests for utils module"""

import logging as log
from src.utils import setup_logs, create_contents, format_date, clean_string
from src.enums import LogLevel


def test_setup_logs():
    """Test setup_logs function"""
    setup_logs(LogLevel.DEBUG)
    assert log.getLogger().level == 30


def test_create_contents():
    """Test create_contents function"""
    input_array = ["Section 1", "Section 2"]
    expected_output = "- [Section 1](#section-1)\n- [Section 2](#section-2)\n"
    assert create_contents(input_array) == expected_output


def test_format_date():
    """Test format_date function"""
    date_str = "2023-06-20T10:20:30.000Z"
    assert format_date(date_str) == "20-06-2023 10:20"

    invalid_date_str = "Invalid date"
    assert format_date(invalid_date_str) == invalid_date_str


def test_clean_string():
    """Test clean_string function"""
    html_string = "<p>This is a test</p>"
    assert clean_string(html_string, 3) == "This is a test"

    url_string = "Visit https://example.com for more info."
    assert clean_string(url_string, 3) == "Visit for more info."

    short_string = "Short"
    assert clean_string(short_string, 10) == ""
