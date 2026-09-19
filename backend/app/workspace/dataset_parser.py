"""
Dataset parser: sniff delimiter, detect encoding, preview rows,
and infer column types for CSV / Excel / Parquet.
"""
import re

import csv
import os
from typing import Any, Dict, List, Optional

import pandas as pd

from app.core.logging import logger


class ParseError(Exception):
    """Raised when a dataset cannot be parsed."""


def detect_encoding(file_path: str) -> str:
    """Try common encodings, return first that works."""
    candidates = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in candidates:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(65536)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def sniff_delimiter(file_path: str, encoding: Optional[str] = None) -> str:
    """Detect CSV delimiter; fallback to comma."""
    enc = encoding or detect_encoding(file_path)
    try:
        with open(file_path, "r", encoding=enc, newline="") as f:
            sample = f.read(8192)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except Exception:
        return ","


def _read_dataframe(file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".csv":
            enc = detect_encoding(file_path)
            sep = sniff_delimiter(file_path, enc)
            return pd.read_csv(
                file_path, encoding=enc, sep=sep, nrows=nrows, low_memory=False
            )
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(file_path, nrows=nrows)
        if ext == ".parquet":
            df = pd.read_parquet(file_path)
            return df.head(nrows) if nrows else df
    except Exception as exc:
        raise ParseError(f"Failed to read {ext}: {exc}") from exc
    raise ParseError(f"Unsupported file extension: {ext}")


def preview(file_path: str, n: int = 100) -> Dict[str, Any]:
    """Return preview rows + column names."""
    df = _read_dataframe(file_path, nrows=n)
    df_clean = df.astype(object).where(pd.notna(df), None)
    rows = df_clean.to_dict(orient="records")
    return {
        "columns": [str(c) for c in df.columns],
        "rows": rows,
        "preview_count": len(rows),
    }


def _infer_type(series: pd.Series) -> str:
    """Infer a coarse type name from a pandas Series."""
    if pd.api.types.is_integer_dtype(series):
        non_null = series.dropna()
        if len(non_null) > 0:
            try:
                max_abs = non_null.abs().max()
                if max_abs > 2_000_000_000:
                    return "bigint"
            except Exception:
                pass
        return "integer"

    if pd.api.types.is_float_dtype(series):
        return "float"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "timestamp"

    non_null = series.dropna()
    if len(non_null) > 0:
        # Only treat as boolean if values are actual Python bools (True/False)
        sample_values = non_null.head(50).tolist()
        if all(isinstance(v, bool) for v in sample_values):
            return "boolean"

        # ISO 8601 timestamp detection (strict)
        sample_str = non_null.head(50).astype(str)
        iso_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?"
        )
        if all(iso_pattern.match(v) for v in sample_str):
            try:
                pd.to_datetime(sample_str, errors="raise")
                return "timestamp"
            except Exception:
                pass

    return "text"


def detect_column_types(
    file_path: str, sample_rows: int = 1000
) -> List[Dict[str, Any]]:
    """Return list of {name, dtype, nullable, sample_values} per column."""
    df = _read_dataframe(file_path, nrows=sample_rows)
    columns = []
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        samples = [str(v) for v in non_null.head(3).tolist()]
        columns.append({
            "name": str(col),
            "dtype": _infer_type(series),
            "nullable": bool(series.isnull().any()),
            "sample_values": samples,
        })
    return columns


def count_rows(file_path: str) -> int:
    """Count total rows in a dataset."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        enc = detect_encoding(file_path)
        with open(file_path, "r", encoding=enc) as f:
            return max(sum(1 for _ in f) - 1, 0)
    return len(_read_dataframe(file_path))