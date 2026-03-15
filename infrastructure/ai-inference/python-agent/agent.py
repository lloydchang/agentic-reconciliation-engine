#!/usr/bin/env python3
"""
Always-On Memory Agent for Qwen2.5 0.5B via Ollama

A lightweight, cost-effective background agent that continuously processes, consolidates, and serves memory.
No vector database. No embeddings. Just an LLM that reads, thinks, and writes structured memory.

Usage:
    python agent.py                          # watch ./inbox, serve on :8888
    python agent.py --watch ./docs --port 9000
    python agent.py --consolidate-every 15   # consolidate every 15 min
"""

import argparse
import asyncio
import json
import logging
import mimetypes
import os
import shutil
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from aiohttp import web

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
DB_PATH = os.getenv("MEMORY_DB", "memory.db")

# Supported file types for ingestion
TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".log", ".xml", ".yaml", ".yml"}
MEDIA_EXTENSIONS = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp", ".svg": "image/svg+xml",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
    ".flac": "audio/flac", ".m4a": "audio/mp4", ".aac": "audio/aac",
    ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
    ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
    ".pdf": "application/pdf",
}
ALL_SUPPORTED = TEXT_EXTENSIONS | set(MEDIA_EXTENSIONS.keys())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="[%H:%M]",
)
log = logging.getLogger("memory-agent")


def ollama_generate(prompt: str, context: str = "") -> str:
    """Generate response from Ollama model."""
    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        }
        if context:
            payload["context"] = context

        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        log.error(f"Ollama API error: {e}")
        return f"Error: {e}"


# Database functions
def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL DEFAULT '',
            raw_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            entities TEXT NOT NULL DEFAULT '[]',
            topics TEXT NOT NULL DEFAULT '[]',
            connections TEXT NOT NULL DEFAULT '[]',
            importance REAL NOT NULL DEFAULT 0.5,
            created_at TEXT NOT NULL,
            consolidated INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS consolidations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ids TEXT NOT NULL,
            summary TEXT NOT NULL,
            insight TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS processed_files (
            path TEXT PRIMARY KEY,
            processed_at TEXT NOT NULL
        );
    """)
    return db


def store_memory(raw_text: str, summary: str, entities: list[str], topics: list[str], importance: float, source: str = "") -> dict:
    """Store a processed memory in the database."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.execute(
        """INSERT INTO memories (source, raw_text, summary, entities, topics, importance, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (source, raw_text, summary, json.dumps(entities), json.dumps(topics), importance, now),
    )
    db.commit()
    mid = cursor.lastrowid
    db.close()
    log.info(f"📥 Stored memory #{mid}: {summary[:60]}...")
    return {"memory_id": mid, "status": "stored", "summary": summary}


def read_all_memories() -> dict:
    """Read all stored memories from the database, most recent first."""
    db = get_db()
    rows = db.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT 50").fetchall()
    memories = []
    for r in rows:
        memories.append({
            "id": r["id"], "source": r["source"], "summary": r["summary"],
            "entities": json.loads(r["entities"]), "topics": json.loads(r["topics"]),
            "importance": r["importance"], "connections": json.loads(r["connections"]),
            "created_at": r["created_at"], "consolidated": bool(r["consolidated"]),
        })
    db.close()
    return {"memories": memories, "count": len(memories)}


def read_unconsolidated_memories() -> dict:
    """Read memories that haven't been consolidated yet."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM memories WHERE consolidated = 0 ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    memories = []
    for r in rows:
        memories.append({
            "id": r["id"], "summary": r["summary"],
            "entities": json.loads(r["entities"]), "topics": json.loads(r["topics"]),
            "importance": r["importance"], "created_at": r["created_at"],
        })
    db.close()
    return {"memories": memories, "count": len(memories)}


def store_consolidation(source_ids: list[int], summary: str, insight: str, connections: list[dict]) -> dict:
    """Store a consolidation result and mark source memories as consolidated."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "INSERT INTO consolidations (source_ids, summary, insight, created_at) VALUES (?, ?, ?, ?)",
        (json.dumps(source_ids), summary, insight, now),
    )
    for conn in connections:
        from_id, to_id = conn.get("from_id"), conn.get("to_id")
        rel = conn.get("relationship", "")
        if from_id and to_id:
            for mid in [from_id, to_id]:
                row = db.execute("SELECT connections FROM memories WHERE id = ?", (mid,)).fetchone()
                if row:
                    existing = json.loads(row["connections"])
                    existing.append({"linked_to": to_id if mid == from_id else from_id, "relationship": rel})
                    db.execute("UPDATE memories SET connections = ? WHERE id = ?", (json.dumps(existing), mid))
    placeholders = ",".join("?" * len(source_ids))
    db.execute(f"UPDATE memories SET consolidated = 1 WHERE id IN ({placeholders})", source_ids)
    db.commit()
    db.close()
    log.info(f"🔄 Consolidated {len(source_ids)} memories. Insight: {insight[:80]}...")
    return {"status": "consolidated", "memories_processed": len(source_ids), "insight": insight}


def read_consolidation_history() -> dict:
    """Read past consolidation insights."""
    db = get_db()
    rows = db.execute("SELECT * FROM consolidations ORDER BY created_at DESC LIMIT 10").fetchall()
    result = [{"summary": r["summary"], "insight": r["insight"], "source_ids": r["source_ids"]} for r in rows]
    db.close()
    return {"consolidations": result, "count": len(result)}


def get_memory_stats() -> dict:
    """Get current memory statistics."""
    db = get_db()
    total = db.execute("SELECT COUNT(*) as c FROM memories").fetchone()["c"]
    unconsolidated = db.execute("SELECT COUNT(*) as c FROM memories WHERE consolidated = 0").fetchone()["c"]
    consolidations = db.execute("SELECT COUNT(*) as c FROM consolidations").fetchone()["c"]
    db.close()
    return {
        "total_memories": total,
        "unconsolidated": unconsolidated,
        "consolidations": consolidations,
    }


def delete_memory(memory_id: int) -> dict:
    """Delete a memory by ID."""
    db = get_db()
    row = db.execute("SELECT 1 FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if not row:
        db.close()
        return {"status": "not_found", "memory_id": memory_id}
    db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    db.commit()
    db.close()
    log.info(f"🗑️  Deleted memory #{memory_id}")
    return {"status": "deleted", "memory_id": memory_id}


def clear_all_memories(inbox_path: str | None = None) -> dict:
    """Delete all memories, consolidations, and inbox files. Full reset."""
    db = get_db()
    mem_count = db.execute("SELECT COUNT(*) as c FROM memories").fetchone()["c"]
    db.execute("DELETE FROM memories")
    db.execute("DELETE FROM consolidations")
    db.execute("DELETE FROM processed_files")
    db.commit()
    db.close()

    files_deleted = 0
    if inbox_path:
        folder = Path(inbox_path)
        if folder.is_dir():
            for f in folder.iterdir():
                if f.name.startswith("."):
                    continue
                try:
                    if f.is_file():
                        f.unlink()
                        files_deleted += 1
                    elif f.is_dir():
                        shutil.rmtree(f)
                        files_deleted += 1
                except OSError as e:
                    log.error(f"Failed to delete {f.name}: {e}")

    log.info(f"🗑️  Cleared all {mem_count} memories, deleted {files_deleted} inbox files")
    return {"status": "cleared", "memories_deleted": mem_count, "files_deleted": files_deleted}


class MemoryAgent:
    """Always-On Memory Agent using Qwen2.5 0.5B via configurable backends"""

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.backends: List[Backend] = []

        # Initialize backends based on configuration priority
        for backend_type in self.config.backend_priority:
            if backend_type == BackendType.OLLAMA:
                try:
                    backend = OllamaBackend(self.config.ollama_url, self.config.model)
                    self.backends.append(backend)
                    log.info(f"✅ Initialized {backend.name()} backend")
                except Exception as e:
                    log.warning(f"Failed to initialize {backend_type.value} backend: {e}")
            elif backend_type == BackendType.LLAMA_CPP:
                if self.config.llama_cpp_model_path:
                    try:
                        backend = LlamaCppBackend(self.config.llama_cpp_model_path)
                        self.backends.append(backend)
                        log.info(f"✅ Initialized {backend.name()} backend")
                    except Exception as e:
                        log.warning(f"Failed to initialize {backend_type.value} backend: {e}")

        if not self.backends:
            raise Exception("No inference backends could be initialized")

    def generate(self, prompt: str) -> str:
        """Generate text using configured backends with automatic fallback."""
        for backend in self.backends:
            try:
                response = backend.generate(prompt)
                log.info(f"✅ Generated response using {backend.name()}")
                return response
            except Exception as e:
                log.warning(f"❌ {backend.name()} backend failed: {e}")
                continue
        raise Exception("All inference backends failed")

    def ingest(self, text: str, source: str = "") -> str:
        """Ingest new information into memory."""
        prompt = f"""You are a Memory Ingest Agent. Process this information into structured memory.

Input: {text}

Extract and return ONLY a JSON object with these fields:
{{
    "summary": "1-2 sentence summary",
    "entities": ["key people/companies/products/concepts"],
    "topics": ["2-4 topic tags"],
    "importance": 0.0-1.0
}}

Be concise and accurate."""

        response = ollama_generate(prompt)
        try:
            data = json.loads(response)
            summary = data.get("summary", "")
            entities = data.get("entities", [])
            topics = data.get("topics", [])
            importance = data.get("importance", 0.5)

            result = store_memory(text, summary, entities, topics, importance, source)
            return f"Stored memory #{result['memory_id']}: {summary}"

        except json.JSONDecodeError:
            # Fallback: store with basic info
            store_memory(text, text[:200] + "...", [], [], 0.5, source)
            return f"Stored memory (fallback): {text[:100]}..."

    def consolidate(self) -> str:
        """Run memory consolidation to find connections and patterns."""
        unconsolidated = read_unconsolidated_memories()

        if unconsolidated["count"] < 2:
            return f"Only {unconsolidated['count']} unconsolidated memories. Need at least 2 for consolidation."

        memories_text = "\n".join([
            f"Memory {m['id']}: {m['summary']} (Entities: {', '.join(m['entities'])}) (Topics: {', '.join(m['topics'])})"
            for m in unconsolidated["memories"]
        ])

        prompt = f"""You are a Memory Consolidation Agent. Analyze these memories and find connections/patterns.

Memories:
{memories_text}

Return ONLY a JSON object with:
{{
    "source_ids": [list of memory IDs],
    "summary": "synthesized summary across memories",
    "insight": "one key pattern/insight discovered",
    "connections": [{{"from_id": id, "to_id": id, "relationship": "description"}}]
}}

Be thorough but concise."""

        response = ollama_generate(prompt)
        try:
            data = json.loads(response)
            source_ids = data.get("source_ids", [])
            summary = data.get("summary", "")
            insight = data.get("insight", "")
            connections = data.get("connections", [])

            if source_ids:
                store_consolidation(source_ids, summary, insight, connections)
                return f"Consolidated {len(source_ids)} memories. Insight: {insight}"
            else:
                return "No consolidation needed."

        except json.JSONDecodeError:
            return f"Consolidation parsing failed. Response: {response[:200]}..."

    def query(self, question: str) -> str:
        """Answer questions using stored memories."""
        memories = read_all_memories()
        consolidations = read_consolidation_history()

        context = "Memories:\n"
        for m in memories["memories"][:20]:  # Limit to recent 20
            context += f"[{m['id']}] {m['summary']} (Source: {m['source']})\n"

        if consolidations["consolidations"]:
            context += "\nConsolidation Insights:\n"
            for c in consolidations["consolidations"][:5]:
                context += f"- {c['insight']}\n"

        prompt = f"""You are a Memory Query Agent. Answer this question using the provided memories and insights.

Question: {question}

{context}

Provide a comprehensive answer citing memory IDs like [1], [2]. If no relevant memories exist, say so."""

        response = ollama_generate(prompt)
        return response

    def status(self) -> str:
        """Get memory system status."""
        stats = get_memory_stats()
        return f"""Memory System Status:
- Total Memories: {stats['total_memories']}
- Unconsolidated: {stats['unconsolidated']}
- Consolidations: {stats['consolidations']}
- Model: {MODEL} via Ollama"""


# HTTP API handlers
def build_http(agent: MemoryAgent, watch_path: str = "./inbox"):
    app = web.Application()

    async def handle_query(request: web.Request):
        q = request.query.get("q", "").strip()
        if not q:
            return web.json_response({"error": "missing ?q= parameter"}, status=400)
        answer = agent.query(q)
        return web.json_response({"question": q, "answer": answer})

    async def handle_ingest(request: web.Request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "invalid JSON"}, status=400)
        text = data.get("text", "").strip()
        if not text:
            return web.json_response({"error": "missing 'text' field"}, status=400)
        source = data.get("source", "api")
        result = agent.ingest(text, source=source)
        return web.json_response({"status": "ingested", "response": result})

    async def handle_consolidate(request: web.Request):
        result = agent.consolidate()
        return web.json_response({"status": "done", "response": result})

    async def handle_status(request: web.Request):
        stats = get_memory_stats()
        return web.json_response(stats)

    async def handle_memories(request: web.Request):
        data = read_all_memories()
        return web.json_response(data)

    async def handle_delete(request: web.Request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "invalid JSON"}, status=400)
        memory_id = data.get("memory_id")
        if not memory_id:
            return web.json_response({"error": "missing 'memory_id' field"}, status=400)
        result = delete_memory(int(memory_id))
        return web.json_response(result)

    async def handle_clear(request: web.Request):
        result = clear_all_memories(inbox_path=watch_path)
        return web.json_response(result)

    app.router.add_get("/query", handle_query)
    app.router.add_post("/ingest", handle_ingest)
    app.router.add_post("/consolidate", handle_consolidate)
    app.router.add_get("/status", handle_status)
    app.router.add_get("/memories", handle_memories)
    app.router.add_post("/delete", handle_delete)
    app.router.add_post("/clear", handle_clear)

    return app


# File watcher
async def watch_folder(agent: MemoryAgent, folder: Path, poll_interval: int = 5):
    """Watch a folder for new files and ingest them."""
    folder.mkdir(parents=True, exist_ok=True)
    db = get_db()
    log.info(f"👁️  Watching: {folder}/")

    while True:
        try:
            for f in sorted(folder.iterdir()):
                if f.name.startswith("."):
                    continue
                suffix = f.suffix.lower()
                if suffix not in ALL_SUPPORTED:
                    continue
                row = db.execute("SELECT 1 FROM processed_files WHERE path = ?", (str(f),)).fetchone()
                if row:
                    continue

                try:
                    if suffix in TEXT_EXTENSIONS:
                        log.info(f"📄 New text file: {f.name}")
                        text = f.read_text(encoding="utf-8", errors="replace")[:10000]
                        if text.strip():
                            agent.ingest(text, source=f.name)
                    else:
                        log.warning(f"⚠️  Skipping media file: {f.name} (media processing not implemented)")
                except Exception as file_err:
                    log.error(f"Error ingesting {f.name}: {file_err}")

                db.execute(
                    "INSERT INTO processed_files (path, processed_at) VALUES (?, ?)",
                    (str(f), datetime.now(timezone.utc).isoformat()),
                )
                db.commit()
        except Exception as e:
            log.error(f"Watch error: {e}")

        await asyncio.sleep(poll_interval)


# Consolidation timer
async def consolidation_loop(agent: MemoryAgent, interval_minutes: int = 30):
    """Run consolidation periodically."""
    log.info(f"🔄 Consolidation: every {interval_minutes} minutes")
    while True:
        await asyncio.sleep(interval_minutes * 60)
        try:
            db = get_db()
            count = db.execute("SELECT COUNT(*) as c FROM memories WHERE consolidated = 0").fetchone()["c"]
            db.close()
            if count >= 2:
                log.info(f"🔄 Running consolidation ({count} unconsolidated memories)...")
                result = agent.consolidate()
                log.info(f"🔄 {result[:100]}")
            else:
                log.info(f"🔄 Skipping consolidation ({count} unconsolidated memories)")
        except Exception as e:
            log.error(f"Consolidation error: {e}")


async def main_async(args):
    agent = MemoryAgent()

    log.info("🧠 Always-On Memory Agent starting")
    log.info(f"   Model: {MODEL} via Ollama")
    log.info(f"   Ollama URL: {OLLAMA_BASE_URL}")
    log.info(f"   Database: {DB_PATH}")
    log.info(f"   Watch: {args.watch}")
    log.info(f"   Consolidate: every {args.consolidate_every}m")
    log.info(f"   API: http://localhost:{args.port}")
    log.info("")

    # Start background tasks
    tasks = [
        asyncio.create_task(watch_folder(agent, Path(args.watch))),
        asyncio.create_task(consolidation_loop(agent, args.consolidate_every)),
    ]

    # Start HTTP server
    app = build_http(agent, watch_path=args.watch)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", args.port)
    await site.start()

    log.info(f"✅ Agent running. Drop files in {args.watch}/ or POST to http://localhost:{args.port}/ingest")
    log.info(f"   Supported: text files (txt, md, json, csv, log, xml, yaml, yml)")
    log.info("")

    # Wait forever
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Always-On Memory Agent - Qwen2.5 0.5B via Ollama")
    parser.add_argument("--watch", default="./inbox", help="Folder to watch for new files (default: ./inbox)")
    parser.add_argument("--port", type=int, default=8888, help="HTTP API port (default: 8888)")
    parser.add_argument("--consolidate-every", type=int, default=30, help="Consolidation interval in minutes (default: 30)")
    args = parser.parse_args()

    # Handle graceful shutdown
    loop = asyncio.new_event_loop()

    def shutdown(sig):
        log.info(f"\n👋 Shutting down (signal {sig})...")
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown, sig)

    try:
        loop.run_until_complete(main_async(args))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        loop.close()
        log.info("🧠 Agent stopped.")


if __name__ == "__main__":
    main()
