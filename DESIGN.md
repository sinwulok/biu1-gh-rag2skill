# Technical Design — biu1-gh-rag2skill

Python-only, local-first RAG pipeline for generating `SKILL.md` files from GitHub repositories.

---

## Architecture overview

```
GitHub Repo
    │
    ▼
[Ingestion]        src/fetcher.py + src/selector.py
    │  Fetch file tree via GitHub API.
    │  Score and select high-value files
    │  (README, docs, source, tests).
    │
    ▼
[Chunking]         src/chunker.py
    │  Split each file into overlapping text chunks.
    │  Markdown: split at headers and paragraphs.
    │  Code: split at function/class boundaries.
    │  Max 50 chunks per file; 800-char chunks, 100-char overlap.
    │
    ▼
[Embedding]        src/embedder.py
    │  Generate dense embeddings using sentence-transformers
    │  (default model: all-MiniLM-L6-v2, 384-dim).
    │  Disk-based cache: skip re-embedding identical text.
    │
    ▼
[Indexing]         src/vector_store.py
    │  Store embeddings in a local FAISS IndexFlatL2.
    │  Index is persisted to .cache/vector_store/ and
    │  reloaded on subsequent runs.
    │
    ▼
[Retrieval]        src/retriever.py
    │  Query: "what is the main skill of this repo?"
    │  Return top-k (default 8) chunks above a similarity
    │  threshold (default 0.3).
    │
    ▼
[Generation]       src/generator_v2.py + src/llm_client.py
    │  Assemble retrieved chunks into a prompt.
    │  Call LLM (OpenAI API or local vLLM server).
    │  Response cached by prompt hash to skip repeated calls.
    │  Falls back to template if no LLM is configured.
    │
    ▼
Output: SKILL.md   (draft — requires human review)
```

---

## Module responsibilities

| Module | Responsibility |
|---|---|
| `src/fetcher.py` | GitHub REST API — file tree, raw content |
| `src/selector.py` | Score files by heuristics; pick highest-value subset |
| `src/chunker.py` | Split text into overlapping chunks; preserve structure |
| `src/embedder.py` | Batch embedding generation; per-chunk disk cache |
| `src/vector_store.py` | FAISS IndexFlatL2 wrapper; save/load from disk |
| `src/retriever.py` | Orchestrate chunk→embed→index→retrieve; build context string |
| `src/llm_client.py` | Unified LLM interface: vLLM (local) or OpenAI (API) |
| `src/generator_v2.py` | v2 pipeline: call retriever, build prompt, call LLM, cache |
| `src/generator.py` | v1 pipeline: simple truncation + OpenAI / template fallback |
| `src/cache.py` | Disk-based response cache keyed by SHA-256 of prompt |
| `src/config.py` | All tunable parameters; reads environment variables |

---

## Caching strategy

Three independent cache layers, all stored under `.cache/` (configurable via `RAG_CACHE_DIR`):

1. **Embedding cache** (`embeddings/`) — keyed by SHA-256 of chunk text.
   Avoids re-embedding identical content across runs.

2. **Vector store cache** (`vector_store/`) — FAISS index persisted per repository.
   Avoids re-indexing on every run.

3. **Response cache** (`responses/`) — keyed by SHA-256 of the full prompt.
   Avoids repeated LLM calls for identical inputs.

Clear all caches with `rm -rf .cache/`.

---

## Design principles

- **Local-first**: FAISS and file-based caching; no databases, no external services required.
- **Minimal dependencies**: sentence-transformers, faiss-cpu, numpy, openai, click, requests.
- **Incremental**: v1 pipeline (default, when `--v2` is omitted) is unchanged; v2 is opt-in via `--v2`.
- **Focused output**: generates a single concise `SKILL.md`, not full project documentation.
- **Python-only**: no Rust, no compiled extensions beyond what pip installs.

---

## Configuration

All defaults live in `src/config.py` and can be overridden by environment variables.
See `configs/config.example.yaml` for a documented reference of all tunable parameters.

Key parameters:

| Parameter | Default | Notes |
|---|---|---|
| `CHUNK_SIZE` | 800 chars | Larger = more context per chunk, slower embedding |
| `CHUNK_OVERLAP` | 100 chars | Prevents context loss at chunk boundaries |
| `MAX_CHUNKS_PER_FILE` | 50 | Prevents large files from dominating retrieval |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Fast, 384-dim; swap for higher quality if needed |
| `TOP_K` | 8 | Number of chunks retrieved per query |
| `MIN_SIMILARITY` | 0.3 | Low-relevance chunks filtered out below this threshold |

---

## Current boundaries

- **Scale**: designed for repositories up to a few thousand files; very large monorepos may hit rate limits or produce noisy results.
- **Languages**: heuristics work best for Python, Markdown, and common web languages; exotic file types are treated as plain text.
- **Single-query retrieval**: one fixed retrieval query is used; multi-query retrieval is not implemented.
- **No re-ranking**: retrieved chunks are not re-ranked after initial retrieval.

---

## Future evolution (not planned, for reference)

- Semantic chunking with LLM guidance.
- Multi-query or HyDE retrieval.
- Secondary re-ranking step.
- Support for additional vector store backends.
- Async embedding and retrieval for large repos.
- Automatic cache eviction policy.
