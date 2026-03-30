# biu1-gh-rag2skill

Convert a GitHub repository into a concise, human-readable OpenClaw-style `SKILL.md`.

## What it does

This tool extracts the most meaningful reusable skill or pattern from a GitHub repository and generates a concise `SKILL.md` summary.

**v1 (simple pipeline):**
1. Fetches the file tree and selects the most relevant files
2. Truncates content to manageable excerpts
3. Generates SKILL.md via OpenAI (or template fallback)

**v2 (RAG pipeline):**
1. Fetches and selects high-value files from the repository
2. Chunks files into meaningful pieces
3. Generates embeddings and indexes them locally (FAISS)
4. Retrieves most relevant chunks via semantic search
5. Generates SKILL.md using retrieved context (supports vLLM or OpenAI)
6. Caches embeddings, vector stores, and responses for efficiency

The result is **concise and human-editable** — a quick summary that captures the core skill or pattern of the repository.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# v1: Simple, fast pipeline
python main.py --repo openai/openai-python

# v2: RAG pipeline with retrieval
python main.py --repo openai/openai-python --v2

# v2 with vLLM (requires local vLLM server)
python main.py --repo openai/openai-python --v2 --use-vllm

# With explicit token and custom output path
python main.py --repo owner/repo --token ghp_... --output my-skill.md
```

**Environment variables:**
- `GITHUB_TOKEN`: GitHub personal access token (optional, raises rate limits)
- `OPENAI_API_KEY`: OpenAI API key (required for LLM generation, otherwise uses template)
- `VLLM_API_BASE`: vLLM server URL (default: `http://localhost:8000/v1`)
- `VLLM_MODEL`: Model name for vLLM (default: `meta-llama/Llama-3.1-8B-Instruct`)
- `RAG_CACHE_DIR`: Cache directory for v2 (default: `.cache`)

## Output format

```md
# Skill Name

## What this skill does
One short paragraph.

## When to use it
- Bullet point
- Bullet point

## Key idea
- Bullet point
- Bullet point

## Important files
- `path/to/file` — brief explanation
```

## Project layout

```
main.py          # CLI entry point with v1/v2 mode selection
src/
  # Core v1 components
  fetcher.py     # GitHub API — fetch file tree and file content
  selector.py    # Score and select high-value files
  generator.py   # v1 generation (OpenAI + template fallback)

  # v2 RAG pipeline components
  config.py      # Configuration for v2 pipeline
  chunker.py     # Split files into meaningful chunks
  embedder.py    # Generate and cache embeddings
  vector_store.py # FAISS-based local vector store
  retriever.py   # RAG retrieval coordinator
  llm_client.py  # LLM client (vLLM + OpenAI support)
  generator_v2.py # v2 generation with RAG
  cache.py       # Response caching

tests/
  test_fetcher.py
  test_selector.py
  test_generator.py
  test_chunker.py
  test_cache.py
  test_retriever.py
```

## V2 Architecture

```
GitHub Repo
   |
   v
[Ingestion]
   - git clone / fetch
   - collect README, docs, source, tests
   - ignore noise
   |
   v
[Chunking]
   - split by markdown sections
   - split by function/class
   - keep file path + line metadata
   |
   v
[Indexing]
   - create embeddings
   - store in vector DB (FAISS)
   - cache embeddings / file hashes
   |
   v
[Retrieval]
   - query: "what is the main skill of this repo?"
   - get top-k chunks
   - optional rerank
   |
   v
[Context Assembly]
   - merge relevant chunks
   - keep short context
   - deduplicate
   |
   v
[LLM Generation via vLLM]
   - generate concise SKILL.md
   - use fixed prompt template
   |
   v
[Postprocess]
   - trim verbosity
   - enforce structure
   - check readability
   |
   v
[Human Review]
   - edit if needed
   |
   v
Output: SKILL.md
```

The v2 pipeline adds retrieval-augmented generation for better context selection:

**Key components:**
- **Chunker**: Splits code and docs into overlapping chunks while preserving structure
- **Embedder**: Uses `sentence-transformers` for local embedding generation with disk cache
- **Vector Store**: FAISS-based similarity search, persisted locally
- **Retriever**: Coordinates chunking → embedding → indexing → retrieval
- **LLM Client**: Unified interface for vLLM (local) and OpenAI (API)
- **Cache**: Three-level caching (embeddings, vector stores, responses)

**Design principles followed:**
- ✅ Simple: Local file-based storage, no complex infrastructure
- ✅ Incremental: v1 still works, v2 is opt-in via `--v2` flag
- ✅ Practical: Caching where it matters (embeddings, responses)
- ✅ Focused: Still generates concise SKILL.md, not full documentation

## Using vLLM (optional)

To use a local LLM via vLLM:

```bash
# Start vLLM server (in another terminal)
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000

# Run with vLLM
export USE_VLLM=true
python main.py --repo owner/repo --v2 --use-vllm
```

Or configure via environment variables in `src/config.py`.

## Caching behavior

V2 caches aggressively to avoid redundant work:

- **Embedding cache**: Chunks with identical text reuse embeddings
- **Vector store cache**: Repository indexes are saved and reloaded
- **Response cache**: Identical prompts return cached LLM responses

Cache location: `.cache/` (configurable via `RAG_CACHE_DIR`)

To clear caches:
```bash
rm -rf .cache/
```

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```
