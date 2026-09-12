import logging

import pytest

from app.agents import optimizer
from app.agents.optimizer import (
    DEFAULT_LIMIT,
    optimize_query,
)


# =============================================================
# ADD LIMIT — no aggregation, no existing LIMIT
# =============================================================

def test_simple_select_gets_limit():
    sql = "SELECT * FROM transactions"
    result = optimize_query(sql)
    assert result == f"SELECT * FROM transactions LIMIT {DEFAULT_LIMIT}"


def test_select_with_where_gets_limit():
    sql = "SELECT id, amount FROM transactions WHERE date > '2024-01-01'"
    result = optimize_query(sql)
    assert result.endswith(f"LIMIT {DEFAULT_LIMIT}")
    assert "WHERE date > '2024-01-01'" in result


def test_select_with_join_gets_limit():
    sql = (
        "SELECT t.id, t.amount "
        "FROM transactions t "
        "JOIN fraud_labels f ON f.transaction_id = t.id"
    )
    result = optimize_query(sql)
    assert result.endswith(f"LIMIT {DEFAULT_LIMIT}")


# =============================================================
# DO NOT ADD LIMIT — already has LIMIT
# =============================================================

def test_existing_limit_uppercase_not_modified():
    sql = "SELECT * FROM transactions LIMIT 500"
    result = optimize_query(sql)
    assert result == sql
    assert result.count("LIMIT") == 1


def test_existing_limit_lowercase_not_modified():
    sql = "SELECT * FROM transactions limit 500"
    result = optimize_query(sql)
    assert result == sql
    assert result.lower().count("limit") == 1


def test_existing_limit_mixedcase_not_modified():
    sql = "SELECT * FROM transactions LiMiT 500"
    result = optimize_query(sql)
    assert result == sql
    assert result.lower().count("limit") == 1


# =============================================================
# DO NOT ADD LIMIT — has aggregation
# =============================================================

def test_count_aggregation_skips_limit():
    sql = "SELECT COUNT(*) FROM transactions"
    result = optimize_query(sql)
    assert result == sql
    assert "LIMIT" not in result.upper()


def test_sum_aggregation_skips_limit():
    sql = "SELECT SUM(amount) FROM transactions"
    result = optimize_query(sql)
    assert "LIMIT" not in result.upper()


def test_avg_aggregation_skips_limit():
    sql = "SELECT AVG(amount) FROM transactions"
    result = optimize_query(sql)
    assert "LIMIT" not in result.upper()


def test_min_aggregation_skips_limit():
    sql = "SELECT MIN(amount) FROM transactions"
    result = optimize_query(sql)
    assert "LIMIT" not in result.upper()


def test_max_aggregation_skips_limit():
    sql = "SELECT MAX(amount) FROM transactions"
    result = optimize_query(sql)
    assert "LIMIT" not in result.upper()


def test_group_by_skips_limit():
    sql = "SELECT category, COUNT(*) FROM transactions GROUP BY category"
    result = optimize_query(sql)
    assert "LIMIT" not in result.upper()


def test_lowercase_aggregation_skips_limit():
    sql = "select count(*) from transactions"
    result = optimize_query(sql)
    assert "LIMIT" not in result.upper()


# =============================================================
# SEMICOLON STRIPPING
# =============================================================

def test_trailing_semicolon_stripped():
    sql = "SELECT * FROM transactions;"
    result = optimize_query(sql)
    assert result == f"SELECT * FROM transactions LIMIT {DEFAULT_LIMIT}"
    assert ";" not in result


def test_multiple_trailing_semicolons_stripped():
    sql = "SELECT * FROM transactions;;;"
    result = optimize_query(sql)
    assert result == f"SELECT * FROM transactions LIMIT {DEFAULT_LIMIT}"
    assert ";" not in result


def test_no_trailing_semicolon_unchanged():
    sql = "SELECT * FROM transactions"
    result = optimize_query(sql)
    assert not result.endswith(";")


# =============================================================
# WHITESPACE
# =============================================================

def test_surrounding_whitespace_stripped():
    sql = "  \n  SELECT * FROM transactions  \n  "
    result = optimize_query(sql)
    assert result == f"SELECT * FROM transactions LIMIT {DEFAULT_LIMIT}"


def test_leading_whitespace_removed():
    sql = "   SELECT 1"
    result = optimize_query(sql)
    assert not result.startswith(" ")
    assert result == f"SELECT 1 LIMIT {DEFAULT_LIMIT}"


# =============================================================
# SELECT * WARNING
# =============================================================

def test_select_star_logs_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="bithere"):
        optimize_query("SELECT * FROM transactions")

    assert "SELECT *" in caplog.text


def test_explicit_columns_no_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="bithere"):
        optimize_query("SELECT id, amount FROM transactions")

    assert "SELECT *" not in caplog.text


def test_select_star_still_returns_query():
    """Warning only — query is still returned, not blocked."""
    sql = "SELECT * FROM transactions"
    result = optimize_query(sql)
    assert result.startswith("SELECT *")


# =============================================================
# LOG INFO WHEN LIMIT ADDED
# =============================================================

def test_added_limit_logs_info(caplog):
    with caplog.at_level(logging.INFO, logger="bithere"):
        optimize_query("SELECT * FROM transactions")

    assert f"Added LIMIT {DEFAULT_LIMIT}" in caplog.text


# =============================================================
# WORD BOUNDARY — LIMIT not matched inside other words
# =============================================================

def test_word_boundary_limit_in_longer_word_not_matched():
    """
    'UNLIMITED' contains 'LIMIT' but as substring, not word.
    \\b should prevent false match.
    """
    sql = "SELECT * FROM users WHERE plan = 'UNLIMITED'"
    result = optimize_query(sql)
    # Since \bLIMIT\b doesn't match UNLIMITED, LIMIT is added
    assert f"LIMIT {DEFAULT_LIMIT}" in result


def test_word_boundary_count_in_longer_word_not_matched():
    """
    'DISCOUNT' contains 'COUNT' but as substring.
    \\b should prevent false match, so LIMIT is added.
    """
    sql = "SELECT * FROM orders WHERE label = 'DISCOUNT'"
    result = optimize_query(sql)
    # No real aggregation, so LIMIT is added
    assert f"LIMIT {DEFAULT_LIMIT}" in result


# =============================================================
# RETURN VALUE
# =============================================================

def test_returns_string():
    result = optimize_query("SELECT 1")
    assert isinstance(result, str)


def test_empty_string_edge_case():
    """
    Empty string passed to optimizer.
    Documents current behavior: returns ' LIMIT 1000'.
    In practice validator rejects empty before optimizer runs.
    """
    result = optimize_query("")
    assert result == f" LIMIT {DEFAULT_LIMIT}"


def test_only_semicolon_edge_case():
    """
    Only semicolons.
    Documents current behavior: all semicolons stripped, then LIMIT added.
    """
    result = optimize_query(";;;")
    assert result == f" LIMIT {DEFAULT_LIMIT}"