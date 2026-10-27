#!/usr/bin/env python3
"""Build the portable FAQ JSON, SQLite database, and SQL seed from faq_source.txt.
Uses only Python's standard library. Re-running rebuilds the derived files.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "faq_source.txt"
JSON_OUT = ROOT / "faq_seed.json"
SQL_OUT = ROOT / "faq_schema_seed.sql"
DB_OUT = ROOT / "faq_ilug_rc_store.sqlite"
SEPARATOR = "━"
HEADING = re.compile(r"❓\s*(\d{2})\.\s*(.+?)\s*$")


def parse_faq(text: str) -> list[dict[str, object]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    headings: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = HEADING.fullmatch(line.strip())
        if match:
            headings.append((index, int(match.group(1)), match.group(2).strip()))

    records: list[dict[str, object]] = []
    for pos, (line_index, source_number, question) in enumerate(headings):
        start = line_index + 1
        while start < len(lines) and (not lines[start].strip() or lines[start].lstrip().startswith(SEPARATOR)):
            start += 1
        end = headings[pos + 1][0] if pos + 1 < len(headings) else len(lines)
        answer_lines = lines[start:end]
        while answer_lines and (not answer_lines[-1].strip() or answer_lines[-1].lstrip().startswith(SEPARATOR)):
            answer_lines.pop()
        answer = "\n".join(answer_lines).strip()
        if not question or not answer:
            raise ValueError(f"FAQ {source_number:02}: empty question or answer")
        records.append({"id": source_number, "source_number": source_number, "question": question, "answer": answer})

    if len(records) != 20:
        raise ValueError(f"Expected 20 FAQ records, parsed {len(records)}")
    if [r["source_number"] for r in records] != list(range(1, 21)):
        raise ValueError("FAQ numbering must be consecutive from 01 to 20")
    return records


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    records = parse_faq(SOURCE.read_text(encoding="utf-8-sig"))
    source_note = "Conteúdo fornecido pela loja; revisar e aprovar antes de publicar."
    payload = {
        "schema_version": 1,
        "locale": "pt-BR",
        "source_file": SOURCE.name,
        "review_status": "pending_business_review",
        "records": [
            {
                **record,
                "locale": "pt-BR",
                "review_status": "pending_business_review",
                "source_file": SOURCE.name,
            }
            for record in records
        ],
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    schema = """PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS faq_entries (
    id INTEGER PRIMARY KEY,
    source_number INTEGER NOT NULL UNIQUE,
    question TEXT NOT NULL CHECK (length(trim(question)) > 0),
    answer TEXT NOT NULL CHECK (length(trim(answer)) > 0),
    locale TEXT NOT NULL DEFAULT 'pt-BR',
    review_status TEXT NOT NULL DEFAULT 'pending_business_review',
    source_file TEXT NOT NULL DEFAULT 'faq_source.txt'
);
CREATE TABLE IF NOT EXISTS dataset_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_faq_entries_source_number ON faq_entries(source_number);
"""
    inserts = [
        "INSERT INTO faq_entries (id, source_number, question, answer, locale, review_status, source_file) VALUES ("
        f"{record['id']}, {record['source_number']}, {sql_quote(str(record['question']))}, "
        f"{sql_quote(str(record['answer']))}, 'pt-BR', 'pending_business_review', 'faq_source.txt');"
        for record in records
    ]
    metadata = [
        "INSERT INTO dataset_metadata (metadata_key, metadata_value) VALUES "
        f"('source_file', {sql_quote(SOURCE.name)});",
        "INSERT INTO dataset_metadata (metadata_key, metadata_value) VALUES "
        f"('source_note', {sql_quote(source_note)});",
        "INSERT INTO dataset_metadata (metadata_key, metadata_value) VALUES "
        "('schema_version', '1');",
    ]
    SQL_OUT.write_text(schema + "\n".join(inserts + metadata) + "\n", encoding="utf-8")

    if DB_OUT.exists():
        DB_OUT.unlink()
    with sqlite3.connect(DB_OUT) as connection:
        connection.executescript(schema)
        connection.executemany(
            "INSERT INTO faq_entries (id, source_number, question, answer, locale, review_status, source_file) "
            "VALUES (?, ?, ?, ?, 'pt-BR', 'pending_business_review', ?)",
            [
                (record["id"], record["source_number"], record["question"], record["answer"], SOURCE.name)
                for record in records
            ],
        )
        connection.executemany(
            "INSERT INTO dataset_metadata (metadata_key, metadata_value) VALUES (?, ?)",
            [("source_file", SOURCE.name), ("source_note", source_note), ("schema_version", "1")],
        )
        count = connection.execute("SELECT COUNT(*) FROM faq_entries").fetchone()[0]
        if count != 20:
            raise RuntimeError(f"Database verification failed: {count} rows")

    print(json.dumps({
        "ok": True,
        "records": len(records),
        "files": [JSON_OUT.name, SQL_OUT.name, DB_OUT.name],
        "review_status": "pending_business_review",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
