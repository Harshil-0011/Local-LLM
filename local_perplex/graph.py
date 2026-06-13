from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .local_perplex_core import tokenize


STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "also",
    "and",
    "any",
    "are",
    "because",
    "been",
    "before",
    "being",
    "between",
    "both",
    "but",
    "can",
    "could",
    "did",
    "does",
    "doing",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "into",
    "its",
    "more",
    "most",
    "not",
    "now",
    "off",
    "only",
    "other",
    "our",
    "out",
    "over",
    "own",
    "same",
    "should",
    "such",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "too",
    "under",
    "very",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json(data: dict | None) -> str:
    return json.dumps(data or {}, ensure_ascii=True, sort_keys=True)


def _load_json(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _clip(value: str, limit: int) -> str:
    value = " ".join((value or "").split())
    return value[:limit]


def _item_get(item, key: str, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


class KnowledgeGraph:
    """Small persistent graph map for local memory and retrieval."""

    def __init__(self, graph_dir: str | Path | None = None, db_path: str | Path | None = None):
        if db_path is None:
            if graph_dir is None:
                graph_dir = os.getenv("LOCAL_PERPLEX_GRAPH_DIR")
                if graph_dir is None:
                    project_root = Path(__file__).parent.parent
                    graph_dir = project_root / "graph"
            graph_dir = Path(graph_dir)
            graph_dir.mkdir(parents=True, exist_ok=True)
            db_path = graph_dir / "knowledge_graph.sqlite3"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    label TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1,
                    evidence TEXT NOT NULL DEFAULT '',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    PRIMARY KEY (source_id, target_id, relation),
                    FOREIGN KEY (source_id) REFERENCES nodes(id),
                    FOREIGN KEY (target_id) REFERENCES nodes(id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")

    @staticmethod
    def extract_terms(text: str, limit: int = 24) -> list[str]:
        counts = Counter(
            token
            for token in tokenize(text)
            if len(token) >= 3 and token not in STOPWORDS and not token.isdigit()
        )
        return [term for term, _ in counts.most_common(limit)]

    @staticmethod
    def node_id(kind: str, label: str) -> str:
        normalized = " ".join((label or "").lower().split())
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
        return f"{kind}:{digest}"

    def upsert_node(
        self,
        kind: str,
        label: str,
        metadata: dict | None = None,
        weight: float = 1.0,
        node_id: str | None = None,
    ) -> str:
        node_id = node_id or self.node_id(kind, label)
        now = _now()
        metadata_json = _json(metadata)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO nodes (id, kind, label, weight, metadata, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    weight = nodes.weight + excluded.weight,
                    label = excluded.label,
                    metadata = CASE
                        WHEN excluded.metadata != '{}' THEN excluded.metadata
                        ELSE nodes.metadata
                    END,
                    last_seen = excluded.last_seen
                """,
                (node_id, kind, label, weight, metadata_json, now, now),
            )
        return node_id

    def upsert_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        evidence: str = "",
    ) -> None:
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO edges (source_id, target_id, relation, weight, evidence, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id, target_id, relation) DO UPDATE SET
                    weight = edges.weight + excluded.weight,
                    evidence = excluded.evidence,
                    last_seen = excluded.last_seen
                """,
                (source_id, target_id, relation, weight, _clip(evidence, 500), now, now),
            )

    def record_research(self, question: str, answer: str, sources: Iterable, tag: str = "General") -> str:
        timestamp = _now()
        session_id = self.upsert_node(
            "research",
            _clip(question, 160) or "Untitled research",
            {
                "question": question,
                "answer": _clip(answer, 3000),
                "tag": tag,
                "timestamp": timestamp,
            },
            node_id=self.node_id("research", f"{timestamp}:{question}"),
        )
        question_id = self.upsert_node("question", question, {"text": question})
        tag_id = self.upsert_node("tag", tag or "General")
        self.upsert_edge(session_id, question_id, "asked", evidence=question)
        self.upsert_edge(session_id, tag_id, "tagged")

        for term in self.extract_terms(f"{question}\n{answer}", limit=32):
            term_id = self.upsert_node("term", term)
            self.upsert_edge(question_id, term_id, "mentions", evidence=question)
            self.upsert_edge(session_id, term_id, "mentions", evidence=answer)

        for source in sources or []:
            title = _item_get(source, "title", "Untitled source") or "Untitled source"
            url = _item_get(source, "url", "") or ""
            content = _item_get(source, "content", "") or _item_get(source, "snippet", "") or ""
            label = title if title != "Untitled source" else url
            source_id = self.upsert_node(
                "source",
                label or "Untitled source",
                {"title": title, "url": url, "snippet": _clip(content, 1200)},
            )
            self.upsert_edge(session_id, source_id, "used_source", evidence=url)
            self.upsert_edge(question_id, source_id, "returned_source", evidence=url)
            for term in self.extract_terms(f"{title}\n{content}", limit=16):
                term_id = self.upsert_node("term", term)
                self.upsert_edge(source_id, term_id, "contains", evidence=title)

        return session_id

    def record_document(self, name: str, content: str) -> str:
        doc_id = self.upsert_node(
            "document",
            name,
            {"name": name, "snippet": _clip(content, 2000), "indexed_at": _now()},
        )
        for term in self.extract_terms(content, limit=48):
            term_id = self.upsert_node("term", term)
            self.upsert_edge(doc_id, term_id, "contains", evidence=name)
        return doc_id

    def context_for_query(self, query: str, limit: int = 8) -> str:
        terms = self.extract_terms(query, limit=12)
        if not terms:
            return ""

        scores: dict[str, float] = defaultdict(float)
        rows_by_id: dict[str, sqlite3.Row] = {}

        with self._connect() as conn:
            for term in terms:
                term_id = self.node_id("term", term)
                rows = conn.execute(
                    """
                    SELECT n.*, e.weight AS edge_weight
                    FROM edges e
                    JOIN nodes n ON n.id = e.source_id
                    WHERE e.target_id = ?
                      AND n.kind IN ('research', 'document', 'source')
                    UNION ALL
                    SELECT n.*, e.weight AS edge_weight
                    FROM edges e
                    JOIN nodes n ON n.id = e.target_id
                    WHERE e.source_id = ?
                      AND n.kind IN ('research', 'document', 'source')
                    """,
                    (term_id, term_id),
                ).fetchall()
                for row in rows:
                    rows_by_id[row["id"]] = row
                    scores[row["id"]] += float(row["edge_weight"] or 1.0)

        if not scores:
            return ""

        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
        grouped: dict[str, list[str]] = {"research": [], "document": [], "source": []}

        for node_id, _ in ordered:
            row = rows_by_id[node_id]
            metadata = _load_json(row["metadata"])
            kind = row["kind"]
            if kind == "research":
                answer = _clip(metadata.get("answer", ""), 700)
                question = metadata.get("question", row["label"])
                grouped[kind].append(f"- Q: {question}\n  Prior answer: {answer}")
            elif kind == "document":
                grouped[kind].append(f"- {row['label']}: {_clip(metadata.get('snippet', ''), 500)}")
            elif kind == "source":
                url = metadata.get("url", "")
                grouped[kind].append(f"- {row['label']} ({url}): {_clip(metadata.get('snippet', ''), 500)}")

        sections = []
        if grouped["research"]:
            sections.append("Related past research:\n" + "\n".join(grouped["research"][:3]))
        if grouped["document"]:
            sections.append("Related local documents:\n" + "\n".join(grouped["document"][:3]))
        if grouped["source"]:
            sections.append("Related remembered sources:\n" + "\n".join(grouped["source"][:3]))

        if not sections:
            return ""
        return "--- GRAPH MEMORY ---\n" + "\n\n".join(sections)

    def stats(self) -> dict:
        with self._connect() as conn:
            node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            kinds = conn.execute(
                "SELECT kind, COUNT(*) AS count FROM nodes GROUP BY kind ORDER BY count DESC"
            ).fetchall()
        return {
            "nodes": node_count,
            "edges": edge_count,
            "kinds": {row["kind"]: row["count"] for row in kinds},
            "path": str(self.db_path),
        }

    def recent_nodes(self, limit: int = 25) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT kind, label, weight, metadata, last_seen
                FROM nodes
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "kind": row["kind"],
                "label": row["label"],
                "weight": row["weight"],
                "metadata": _load_json(row["metadata"]),
                "last_seen": row["last_seen"],
            }
            for row in rows
        ]
