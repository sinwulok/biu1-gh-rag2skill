#!/usr/bin/env python3
"""CLI entry point for biu1-gh-rag2skill."""

import sys

import click

from src.fetcher import fetch_repo_files, fetch_file_content
from src.selector import select_files, truncate_content
from src.generator import generate_skill_md
from src.generator_v2 import generate_skill_md_v2


@click.command()
@click.option(
    "--repo",
    required=True,
    help="GitHub repository as owner/repo or full URL (e.g. openai/openai-python).",
)
@click.option(
    "--output",
    default="SKILL.md",
    show_default=True,
    help="Path for the generated SKILL.md file.",
)
@click.option(
    "--token",
    envvar="GITHUB_TOKEN",
    default=None,
    help="GitHub personal access token (or set GITHUB_TOKEN env var).",
)
@click.option(
    "--v2",
    is_flag=True,
    default=False,
    help="Use v2 RAG pipeline (chunking, embeddings, retrieval).",
)
@click.option(
    "--use-vllm",
    is_flag=True,
    default=False,
    help="Use vLLM for generation (v2 only).",
)
def main(repo: str, output: str, token: str, v2: bool, use_vllm: bool) -> None:
    """Convert a GitHub repository into a concise SKILL.md file.

    Examples:

        # v1 (simple, fast)
        python main.py --repo openai/openai-python

        # v2 with RAG pipeline
        python main.py --repo openai/openai-python --v2

        # v2 with vLLM
        python main.py --repo openai/openai-python --v2 --use-vllm
    """
    # Normalize repo reference (accept full GitHub URLs too)
    repo_ref = repo.replace("https://github.com/", "").rstrip("/")

    click.echo(f"Fetching file tree for {repo_ref} …")
    try:
        all_files = fetch_repo_files(repo_ref, token=token)
    except Exception as exc:
        click.echo(f"Error fetching repository: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Found {len(all_files)} files. Selecting most relevant …")
    selected = select_files(all_files)

    if not selected:
        click.echo("No relevant files found. Exiting.", err=True)
        sys.exit(1)

    click.echo(f"Selected {len(selected)} files. Fetching content …")
    for f in selected:
        content = fetch_file_content(repo_ref, f["path"], token=token)
        f["content"] = truncate_content(content) if content else None

    # Choose generation pipeline
    if v2:
        click.echo("Using v2 RAG pipeline for generation …")
        skill_md = generate_skill_md_v2(repo_ref, selected, use_vllm=use_vllm)
    else:
        click.echo("Using v1 pipeline for generation …")
        skill_md = generate_skill_md(repo_ref, selected)

    with open(output, "w", encoding="utf-8") as fh:
        fh.write(skill_md)

    click.echo(f"Done! SKILL.md written to {output}")
    click.echo("Review and edit the file as needed.")


if __name__ == "__main__":
    main()
