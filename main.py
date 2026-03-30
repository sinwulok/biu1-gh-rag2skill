#!/usr/bin/env python3
"""CLI entry point for biu1-gh-rag2skill."""

import sys

import click

from src.fetcher import fetch_repo_files, fetch_file_content
from src.selector import select_files, truncate_content
from src.generator import generate_skill_md


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
def main(repo: str, output: str, token: str) -> None:
    """Convert a GitHub repository into a concise SKILL.md file.

    Example:

        python main.py --repo openai/openai-python --output SKILL.md
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

    click.echo("Generating SKILL.md …")
    skill_md = generate_skill_md(repo_ref, selected)

    with open(output, "w", encoding="utf-8") as fh:
        fh.write(skill_md)

    click.echo(f"Done! SKILL.md written to {output}")
    click.echo("Review and edit the file as needed.")


if __name__ == "__main__":
    main()
