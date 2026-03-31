# biu1-gh-rag2skill

A Python CLI that reads a GitHub repository and drafts a concise `SKILL.md` using lightweight RAG.

## Why it exists

Summarizing an unfamiliar repository well enough to reuse it is slow.
This tool automates the first pass: it fetches the most relevant files, retrieves the most relevant chunks via semantic search, and asks an LLM to produce a structured one-page skill card.
The output is a **draft** — always review and edit before treating it as authoritative.

## What it does

1. Fetches the file tree and selects high-value files (README, docs, source, tests).
2. Chunks files into overlapping segments; generates local embeddings (sentence-transformers).
3. Indexes chunks in a local FAISS vector store; retrieves the top-k most relevant ones.
4. Sends retrieved context to an LLM (OpenAI API or local vLLM) to generate a structured `SKILL.md`.
5. Caches embeddings, vector stores, and LLM responses so repeated runs are fast.

## What it does not do

- Does not generate full project documentation.
- Does not commit or push anything; writes output to the local filesystem only.
- Does not guarantee correctness — the generated skill card is a starting point, not a finished artefact.

## Quick start

```bash
# 1. Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Set your API key (or use a local vLLM server — see below)
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...   # optional, raises rate limits

# 3. Run
python main.py --repo openai/openai-python        # simple pipeline
python main.py --repo openai/openai-python --v2   # RAG pipeline (recommended)

# Custom output path
python main.py --repo owner/repo --v2 --output my-skill.md
```

The generated file is a draft — **review and edit it** before use.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | _(none)_ | GitHub PAT — raises API rate limits |
| `OPENAI_API_KEY` | _(none)_ | Required for LLM generation; falls back to template if unset |
| `VLLM_API_BASE` | `http://localhost:8000/v1` | vLLM server URL |
| `VLLM_MODEL` | `meta-llama/Llama-3.1-8B-Instruct` | Model name for vLLM |
| `RAG_CACHE_DIR` | `.cache` | Cache directory for embeddings and responses |

## Using a local LLM (vLLM)

```bash
# In a separate terminal, start vLLM
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000

# Then run with --use-vllm
python main.py --repo owner/repo --v2 --use-vllm
```

## Repository layout

```
main.py               # CLI entry point
requirements.txt
pyproject.toml

src/
  fetcher.py          # GitHub API — fetch file tree and content
  selector.py         # Score and select high-value files
  generator.py        # v1 generation (OpenAI + template fallback)
  config.py           # Tunable parameters for v2 pipeline
  chunker.py          # Split files into overlapping chunks
  embedder.py         # Local embeddings via sentence-transformers
  vector_store.py     # FAISS-based local vector store
  retriever.py        # RAG coordinator (chunk → embed → index → retrieve)
  llm_client.py       # Unified LLM interface (vLLM + OpenAI)
  generator_v2.py     # v2 generation with RAG context
  cache.py            # Response caching (disk-based)

configs/
  config.example.yaml # Example configuration with all defaults

tests/
  test_fetcher.py
  test_selector.py
  test_generator.py
  test_chunker.py
  test_cache.py
  test_retriever.py
```

See [`DESIGN.md`](DESIGN.md) for the full technical design.

## Running tests

```bash
python -m pytest tests/ -v
```
