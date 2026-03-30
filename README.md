# biu1-gh-rag2skill

Convert a GitHub repository into a concise, human-readable OpenClaw-style `SKILL.md`.

## What it does

1. Fetches the file tree of any public (or private, with a token) GitHub repository.
2. Scores and selects the most relevant files — READMEs, docs, top-level source files — while ignoring noise like `node_modules`, lock files, and generated artefacts.
3. Fetches the content of those files and truncates each to a manageable excerpt.
4. Sends the context to an OpenAI model (falls back to a template when no API key is set) to generate a short `SKILL.md`.

The result is **concise and human-editable** — a quick summary that captures the core skill or pattern of the repository.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Run (uses GITHUB_TOKEN env var if set)
python main.py --repo openai/openai-python

# With explicit token and custom output path
python main.py --repo owner/repo --token ghp_... --output my-skill.md
```

Set `OPENAI_API_KEY` in your environment to enable LLM-powered generation.  
Without it, a template-based SKILL.md is produced instead.

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
main.py          # CLI entry point
src/
  fetcher.py     # GitHub API — fetch file tree and file content
  selector.py    # Score and select high-value files
  generator.py   # Generate SKILL.md (OpenAI + template fallback)
tests/
  test_fetcher.py
  test_selector.py
  test_generator.py
```

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```
