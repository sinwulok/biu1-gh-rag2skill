"""Generate a SKILL.md from selected repository files."""

import os
from typing import Optional

_SKILL_MD_SYSTEM_PROMPT = (
    "You are a technical writer creating concise SKILL.md files for the OpenClaw "
    "framework. Be brief, high-signal, and use simple language."
)

_SKILL_MD_USER_PROMPT = """\
Based on the repository context below, generate a short, readable SKILL.md.

Rules:
- Keep it concise — no verbose prose.
- Focus on the single core skill or pattern this repository demonstrates.
- Use simple bullet points.
- Do not include any text before or after the markdown.

Required output format (fill in every section):

# [Skill Name]

## What this skill does
[One short paragraph — two or three sentences maximum.]

## When to use it
- [bullet]
- [bullet]
- [bullet]

## Key idea
- [bullet]
- [bullet]
- [bullet]

## Important files
- `[path]` — [brief explanation]
- `[path]` — [brief explanation]

---

Repository context:
{context}
"""


def generate_skill_md(repo: str, files: list) -> str:
    """Generate SKILL.md content from a list of selected repository files.

    Tries OpenAI first and falls back to a local template if the API is
    unavailable or an error occurs.

    Args:
        repo: Owner/repo string (e.g. ``"openai/openai-python"``).
        files: List of file dicts with at least ``path`` and ``content`` keys.

    Returns:
        SKILL.md content as a string.
    """
    try:
        return _generate_with_openai(repo, files)
    except Exception:
        return _generate_template(repo, files)


def _build_context(repo: str, files: list) -> str:
    """Build a compact context string from selected files."""
    parts = [f"Repository: {repo}\n"]
    for f in files:
        content = f.get("content") or "(content unavailable)"
        parts.append(f"=== {f['path']} ===\n{content}\n")
    return "\n".join(parts)


def _generate_with_openai(repo: str, files: list) -> str:
    """Generate SKILL.md using the OpenAI chat API."""
    import openai  # Imported lazily so the module works without openai installed.

    context = _build_context(repo, files)
    user_message = _SKILL_MD_USER_PROMPT.format(context=context)

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SKILL_MD_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=800,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _generate_template(repo: str, files: list) -> str:
    """Generate a template-based SKILL.md without an LLM."""
    repo_name = repo.split("/")[-1]

    readme_excerpt = ""
    for f in files:
        if os.path.basename(f["path"]).lower().startswith("readme") and f.get("content"):
            readme_excerpt = f["content"][:300].strip()
            break

    important_files_lines = "\n".join(
        f"- `{f['path']}` — review this file" for f in files[:5]
    )

    what_it_does = (
        f"Based on `{repo}`. {readme_excerpt}" if readme_excerpt else f"Based on the `{repo}` GitHub repository."
    )

    return f"""\
# {repo_name}

## What this skill does
{what_it_does}

## When to use it
- When you need the patterns demonstrated in {repo_name}
- When solving problems similar to those addressed in this repository
- When referencing this codebase as an implementation guide

## Key idea
- Review the repository README for the main concept
- Check the important files below for implementation details
- Adapt the patterns to your specific use case

## Important files
{important_files_lines}
"""
