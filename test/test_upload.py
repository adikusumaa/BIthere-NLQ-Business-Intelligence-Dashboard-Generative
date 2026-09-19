"""
Tests for file upload + dataset parser (CSV, Excel, Parquet).
"""

import io
import os
import pytest
import pandas as pd

from fastapi import UploadFile

from app.workspace import upload as upload_mod
from app.workspace import dataset_parser as parser_mod


@pytest.fixture
def sample_csv(tmp_path) -> str:
    path = tmp_path / "sample.csv"
    path.write_text(
        "id,name,amount,created_at,is_active\n"
        "1,Alice,100.5,2024-01-01,true\n"
        "2,Bob,200.0,2024-01-02,false\n"
        "3,Carol,,2024-01-03,true\n",
        encoding="utf-8",
    )
    return str(path)


@pytest.fixture
def sample_excel(tmp_path) -> str:
    path = tmp_path / "sample.xlsx"
    pd.DataFrame({"id": [1, 2], "name": ["A", "B"]}).to_excel(path, index=False)
    return str(path)


@pytest.fixture
def sample_parquet(tmp_path) -> str:
    path = tmp_path / "sample.parquet"
    pd.DataFrame({"id": [1, 2, 3], "value": [1.5, 2.5, 3.5]}).to_parquet(path, index=False)
    return str(path)


# ============ upload ============

async def test_save_csv_upload(tmp_path, monkeypatch):
    monkeypatch.setattr("app.workspace.upload.settings.UPLOAD_DIR", str(tmp_path))

    content = b"id,name\n1,a\n2,b\n"
    file = UploadFile(filename="data.csv", file=io.BytesIO(content))

    result = await upload_mod.save_upload("ws-1", file)
    assert result["extension"] == ".csv"
    assert result["size_bytes"] == len(content)
    assert os.path.exists(result["stored_path"])


async def test_save_upload_rejects_bad_extension(tmp_path, monkeypatch):
    monkeypatch.setattr("app.workspace.upload.settings.UPLOAD_DIR", str(tmp_path))
    file = UploadFile(filename="data.exe", file=io.BytesIO(b"x"))

    with pytest.raises(upload_mod.UploadError):
        await upload_mod.save_upload("ws-1", file)


async def test_save_upload_rejects_oversize(tmp_path, monkeypatch):
    monkeypatch.setattr("app.workspace.upload.settings.UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("app.workspace.upload.settings.MAX_UPLOAD_SIZE_MB", 0)

    file = UploadFile(filename="data.csv", file=io.BytesIO(b"id\n1\n"))
    with pytest.raises(upload_mod.UploadError):
        await upload_mod.save_upload("ws-1", file)


async def test_save_upload_no_filename(tmp_path, monkeypatch):
    monkeypatch.setattr("app.workspace.upload.settings.UPLOAD_DIR", str(tmp_path))
    file = UploadFile(filename="", file=io.BytesIO(b"x"))

    with pytest.raises(upload_mod.UploadError):
        await upload_mod.save_upload("ws-1", file)


def test_delete_upload(sample_csv):
    assert os.path.exists(sample_csv)
    assert upload_mod.delete_upload(sample_csv) is True
    assert not os.path.exists(sample_csv)
    assert upload_mod.delete_upload(sample_csv) is False


# ============ parser ============

def test_detect_encoding_csv(sample_csv):
    enc = parser_mod.detect_encoding(sample_csv)
    assert enc in ("utf-8", "utf-8-sig")


def test_sniff_delimiter_comma(sample_csv):
    assert parser_mod.sniff_delimiter(sample_csv) == ","


def test_sniff_delimiter_semicolon(tmp_path):
    path = tmp_path / "semi.csv"
    path.write_text(
        "id;name;amount\n1;A;10\n2;B;20\n3;C;30\n4;D;40\n",
        encoding="utf-8",
    )
    assert parser_mod.sniff_delimiter(str(path)) == ";"


def test_preview_csv(sample_csv):
    result = parser_mod.preview(sample_csv, n=10)
    assert result["preview_count"] == 3
    assert "id" in result["columns"]
    assert result["rows"][0]["name"] == "Alice"


def test_detect_column_types_csv(sample_csv):
    cols = parser_mod.detect_column_types(sample_csv)
    types = {c["name"]: c["dtype"] for c in cols}
    assert types["id"] == "integer"
    assert types["amount"] == "float"
    assert types["is_active"] == "boolean"
    assert types["name"] == "text"
    assert types["created_at"] == "timestamp"


def test_count_rows_csv(sample_csv):
    assert parser_mod.count_rows(sample_csv) == 3


def test_preview_excel(sample_excel):
    result = parser_mod.preview(sample_excel, n=10)
    assert result["preview_count"] == 2
    assert "id" in result["columns"]


def test_preview_parquet(sample_parquet):
    result = parser_mod.preview(sample_parquet, n=10)
    assert result["preview_count"] == 3
    assert "value" in result["columns"]


def test_detect_column_types_parquet(sample_parquet):
    cols = parser_mod.detect_column_types(sample_parquet)
    types = {c["name"]: c["dtype"] for c in cols}
    assert types["id"] == "integer"
    assert types["value"] == "float"


def test_unsupported_extension_raises(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("hello")
    with pytest.raises(parser_mod.ParseError):
        parser_mod.preview(str(path))