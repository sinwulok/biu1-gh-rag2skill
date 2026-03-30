"""V2 generator using RAG pipeline.

Uses retrieval-augmented generation to create SKILL.md:
1. Index repository files into vector store
2. Retrieve most relevant chunks based on repository context
3. Generate SKILL.md using LLM with retrieved context
"""

from typing import List, Dict

from src.retriever import Retriever, build_context_from_chunks
from src.llm_client import create_client
from src.cache import get_cached_response, save_cached_response, create_prompt_key


_SKILL_MD_SYSTEM_PROMPT = (
    "You are a technical writer creating concise SKILL.md files for the OpenClaw "
    "framework. Be brief, high-signal, and use simple language."
)

_SKILL_MD_USER_PROMPT_V2 = """\
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

Repository: {repo}

Retrieved context (most relevant chunks):
{context}
"""


def generate_skill_md_v2(
    repo: str,
    files: List[Dict[str, any]],
    use_vllm: bool = False,
) -> str:
    """Generate SKILL.md using v2 RAG pipeline.

    Args:
        repo: Owner/repo string (e.g., "openai/openai-python").
        files: List of file dicts with 'path' and 'content' keys.
        use_vllm: Whether to use vLLM for generation.

    Returns:
        SKILL.md content as a string.
    """
    # Initialize retriever
    retriever = Retriever(repo)

    # Try loading from cache first
    if retriever.load():
        print(f"Loaded vector store from cache for {repo}")
    else:
        print(f"Indexing {len(files)} files into vector store...")
        retriever.index_files(files)
        retriever.save()
        print(f"Indexed and saved vector store for {repo}")

    # Retrieve relevant context
    # Query is designed to find the most important implementation details
    query = (
        f"What is the main skill, pattern, or implementation approach in {repo}? "
        "What are the key components and how do they work?"
    )
    chunks = retriever.retrieve(query)
    print(f"Retrieved {len(chunks)} relevant chunks")

    # Build context string
    context = build_context_from_chunks(chunks)

    # Generate SKILL.md
    user_prompt = _SKILL_MD_USER_PROMPT_V2.format(repo=repo, context=context)

    # Check cache
    prompt_key = create_prompt_key(_SKILL_MD_SYSTEM_PROMPT, user_prompt)
    cached = get_cached_response(prompt_key)
    if cached:
        print("Using cached response")
        return cached

    # Generate with LLM
    print("Generating SKILL.md with LLM...")
    client = create_client(use_vllm=use_vllm)
    try:
        response = client.generate(_SKILL_MD_SYSTEM_PROMPT, user_prompt)
        save_cached_response(prompt_key, response)
        return response
    except Exception as e:
        print(f"LLM generation failed: {e}")
        print("Falling back to template-based generation...")
        # Fall back to v1 template generation
        from src.generator import _generate_template
        return _generate_template(repo, files)
