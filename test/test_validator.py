import pytest

from app.agents import validator
from app.agents.validator import QueryValidationError, validate_query


# =============================================================
# HAPPY PATH
# =============================================================

def test_simple_select_passes():
    sql = "SELECT * FROM users LIMIT 10"
    assert validate_query(sql) == sql


def test_select_with_join_passes():
    sql = (
        "SELECT t.id, t.amount "
        "FROM transactions t "
        "JOIN fraud_labels f ON f.transaction_id = t.id "
        "LIMIT 1000"
    )
    assert validate_query(sql) == sql


def test_select_with_aggregation_passes():
    sql = "SELECT COUNT(*) FROM transactions"
    assert validate_query(sql) == sql


def test_cte_query_passes():
    """WITH clause queries are allowed."""
    sql = (
        "WITH fraud AS (SELECT * FROM fraud_labels WHERE fraud_label = 'fraud') "
        "SELECT COUNT(*) FROM fraud"
    )
    assert validate_query(sql) == sql


def test_lowercase_select_passes():
    sql = "select * from users limit 10"
    assert validate_query(sql) == sql


def test_mixed_case_select_passes():
    sql = "SeLeCt * FrOm users"
    assert validate_query(sql) == sql


def test_trailing_semicolon_passes():
    sql = "SELECT 1;"
    assert validate_query(sql) == sql


# =============================================================
# EMPTY / WHITESPACE
# =============================================================

def test_empty_string_raises():
    with pytest.raises(QueryValidationError, match="Empty query"):
        validate_query("")


def test_none_raises():
    with pytest.raises(QueryValidationError, match="Empty query"):
        validate_query(None)


def test_whitespace_only_raises():
    with pytest.raises(QueryValidationError, match="Empty query"):
        validate_query("   \n\t  ")


# =============================================================
# LENGTH LIMIT
# =============================================================

def test_query_at_max_length_passes():
    """Exactly MAX_QUERY_LENGTH is allowed."""
    prefix = "SELECT '"
    suffix = "' AS x"
    padding = "a" * (validator.MAX_QUERY_LENGTH - len(prefix) - len(suffix))
    sql = f"{prefix}{padding}{suffix}"
    assert len(sql) == validator.MAX_QUERY_LENGTH
    assert validate_query(sql) == sql


def test_query_exceeding_max_length_raises():
    sql = "SELECT '" + ("a" * validator.MAX_QUERY_LENGTH) + "'"
    with pytest.raises(QueryValidationError, match="exceeds"):
        validate_query(sql)


# =============================================================
# MUST START WITH SELECT / WITH
# =============================================================

def test_query_not_starting_with_select_raises():
    with pytest.raises(QueryValidationError, match="Only SELECT or WITH"):
        validate_query("EXPLAIN SELECT 1")


def test_random_gibberish_raises():
    with pytest.raises(QueryValidationError, match="Only SELECT or WITH"):
        validate_query("hello world")


def test_query_starting_with_comment_then_select_raises():
    """
    Query beginning with a comment then SELECT is rejected because
    the check uses simple startswith, not comment-stripping.
    Documents current behavior.
    """
    sql = "-- comment\nSELECT 1"
    with pytest.raises(QueryValidationError, match="Only SELECT or WITH"):
        validate_query(sql)


# =============================================================
# FORBIDDEN KEYWORDS
# =============================================================

def test_drop_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: DROP"):
        validate_query("DROP TABLE users")


def test_delete_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: DELETE"):
        validate_query("DELETE FROM users")


def test_truncate_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: TRUNCATE"):
        validate_query("TRUNCATE TABLE users")


def test_update_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: UPDATE"):
        validate_query("UPDATE users SET name = 'x'")


def test_insert_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: INSERT"):
        validate_query("INSERT INTO users VALUES (1)")


def test_alter_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: ALTER"):
        validate_query("ALTER TABLE users ADD COLUMN x INT")


def test_create_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: CREATE"):
        validate_query("CREATE TABLE users (id INT)")


def test_grant_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: GRANT"):
        validate_query("GRANT ALL ON users TO admin")


def test_revoke_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: REVOKE"):
        validate_query("REVOKE ALL ON users FROM admin")


def test_exec_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: EXEC"):
        validate_query("EXEC sp_something")


def test_attach_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: ATTACH"):
        validate_query("ATTACH DATABASE foo")


def test_detach_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: DETACH"):
        validate_query("DETACH DATABASE foo")


def test_merge_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: MERGE"):
        validate_query("MERGE INTO users USING src ON ...")


def test_call_raises():
    with pytest.raises(QueryValidationError, match="Forbidden keyword: CALL"):
        validate_query("CALL my_procedure()")


def test_forbidden_keyword_inside_select_raises():
    """SELECT containing DROP as a word is blocked."""
    with pytest.raises(QueryValidationError, match="Forbidden keyword: DROP"):
        validate_query("SELECT * FROM users WHERE action = 'DROP'")


def test_forbidden_keyword_lowercase_raises():
    """Lowercase forbidden keyword is still caught."""
    with pytest.raises(QueryValidationError, match="Forbidden keyword: DROP"):
        validate_query("drop table users")


# =============================================================
# MULTI-STATEMENT
# =============================================================

def test_multiple_statements_raises():
    """Multi-statement without forbidden keywords is caught by statement check."""
    with pytest.raises(QueryValidationError, match="Multiple statements"):
        validate_query("SELECT 1; SELECT 2")


def test_multiple_statements_with_forbidden_keyword_raises_forbidden():
    """
    With the current order, forbidden keyword check runs BEFORE
    multi-statement check. So 'SELECT 1; DROP ...' raises
    'Forbidden keyword: DROP', not 'Multiple statements'.

    Both behaviors are safe — query is rejected either way.
    Documents current behavior.
    """
    with pytest.raises(QueryValidationError, match="Forbidden keyword: DROP"):
        validate_query("SELECT 1; DROP TABLE users;")


def test_single_statement_with_trailing_semicolon_passes():
    sql = "SELECT 1;"
    assert validate_query(sql) == sql


# =============================================================
# RETURN VALUE
# =============================================================

def test_return_value_is_original_sql():
    """validate_query must return the ORIGINAL sql, not the normalized one."""
    sql = "select * from users"
    result = validate_query(sql)
    assert result == sql
    assert result != sql.upper()


# =============================================================
# EDGE CASES
# =============================================================

def test_only_select_no_table_passes():
    sql = "SELECT 1"
    assert validate_query(sql) == sql


def test_with_only_cte_passes():
    sql = "WITH x AS (SELECT 1) SELECT * FROM x"
    assert validate_query(sql) == sql


def test_word_boundary_prevents_false_positive():
    """
    'DROPPED' should NOT trigger DROP detection because of \\b word boundary.
    """
    sql = "SELECT * FROM logs WHERE status = 'DROPPED'"
    assert validate_query(sql) == sql


def test_created_at_column_does_not_trigger_create():
    """'CREATED_AT' column name should not trigger CREATE keyword."""
    sql = "SELECT created_at FROM users"
    assert validate_query(sql) == sql


def test_last_updated_column_does_not_trigger_update():
    """'UPDATED_AT' should not trigger UPDATE keyword."""
    sql = "SELECT updated_at FROM users"
    assert validate_query(sql) == sql