# biu1-gh-rag2skill

## What this tool does

Reads a public GitHub repository and drafts a concise `SKILL.md` — a one-page structured summary of the repository's core skill or pattern.
Uses a lightweight local RAG pipeline (sentence-transformers + FAISS) to select the most relevant content before calling an LLM.

## When to use it

- You want a quick, structured overview of an unfamiliar repository.
- You are building a library of reusable skill cards for agents or developers.
- You want a starting point for manually writing a `SKILL.md`.

## Key idea

Fetch → select → chunk → embed → retrieve → generate → human review.
All intermediate data (embeddings, vector stores, LLM responses) is cached locally to make repeated runs fast.

## Important files

- `main.py` — CLI entry point; `--v2` flag enables the RAG pipeline
- `src/retriever.py` — RAG coordinator (chunk → embed → index → retrieve)
- `src/generator_v2.py` — v2 generation with retrieved context
- `src/config.py` — all tunable parameters
- `configs/config.example.yaml` — example configuration with documented defaults

## Limitations / review expectations

- The generated `SKILL.md` is a **draft**. Always review and edit before treating it as authoritative.
- Quality depends on repository structure and LLM quality. Repos with clear READMEs and docs produce better results.
- The tool does not access private repositories unless a `GITHUB_TOKEN` with appropriate permissions is provided.
- No Rust, no distributed systems, no cloud-native dependencies — Python-only, runs locally.
