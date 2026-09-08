"""
Metadata ingestion script for BIthere.
Reads database schema from Supabase, combines with business glossary,
generates embeddings, and upserts to Pinecone.
"""

import asyncio
import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from supabase import create_client

from app.core.config import settings
from app.core.logging import logger
from app.rag.embedding import embed_text
from app.rag.pinecone_client import pinecone_client

SOURCE_TABLES = ["users", "cards", "mcc_codes", "transactions", "fraud_labels"]


def get_supabase_client():
    """
    Returns Supabase client with service role key.
    """

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def fetch_table_columns(supabase, table: str) -> list:
    """
    Fetches column names from a table using limit 1 sample.
    """

    response = supabase.table(table).select("*").limit(1).execute()
    if not response.data:
        return []
    sample = response.data[0]
    return list(sample.keys())


async def ingest_schema(supabase) -> None:
    """
    Ingest table and column metadata into Pinecone namespace 'schema'.
    """

    vectors = []

    for table in SOURCE_TABLES:
        columns = fetch_table_columns(supabase, table)
        for column in columns:
            metadata_text = f"table: {table}, column: {column}, type: unknown"
            embedding = await embed_text(metadata_text)
            vectors.append({
                "id": f"schema:{table}:{column}",
                "values": embedding,
                "metadata": {
                    "type": "schema",
                    "table": table,
                    "column": column,
                    "text": metadata_text,
                },
            })

    if vectors:
        pinecone_client.upsert(vectors, namespace="schema")


async def ingest_glossary() -> None:
    """
    Ingest business glossary from CSV into Pinecone namespace 'glossary'.
    """

    csv_path = Path(__file__).resolve().parent / "seed_glossary.csv"
    vectors = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            term = row["term"].strip()
            definition = row["definition"].strip()
            category = row["category"].strip()
            text = f"term: {term}, definition: {definition}, category: {category}"
            embedding = await embed_text(text)
            vectors.append({
                "id": f"glossary:{term}",
                "values": embedding,
                "metadata": {
                    "type": "glossary",
                    "term": term,
                    "definition": definition,
                    "category": category,
                    "text": text,
                },
            })

    if vectors:
        pinecone_client.upsert(vectors, namespace="glossary")


async def main() -> None:
    """
    Main ingestion flow.
    """

    logger.process("Starting metadata ingestion to Pinecone")
    supabase = get_supabase_client()

    await ingest_schema(supabase)
    await ingest_glossary()

    logger.success("Metadata ingestion completed")


if __name__ == "__main__":
    asyncio.run(main())