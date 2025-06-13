"""Command-line interface for wwdc."""

import click
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="wwdc")
@click.option("-y", "--year", type=int, default=datetime.now().year, help="WWDC year")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, year: int, verbose: bool) -> None:
    """WWDC toolkit - download, list, summarize, and export Apple Developer content."""
    ctx.ensure_object(dict)
    ctx.obj["year"] = year
    # Always use ~/.wwdc as the directory
    ctx.obj["directory"] = Path.home() / ".wwdc"
    ctx.obj["verbose"] = verbose
    
    # Ensure the directory exists
    ctx.obj["directory"].mkdir(exist_ok=True)


@cli.command()
@click.option("-s", "--session", help="Session ID(s), comma-separated")
@click.option("-t", "--topic", help='Topic name or "all"')
@click.option("--text-only", is_flag=True, help="Skip video downloads")
@click.option("--force", is_flag=True, help="Re-download existing files")
@click.pass_context
def download(
    ctx: click.Context,
    session: Optional[str],
    topic: Optional[str],
    text_only: bool,
    force: bool,
) -> None:
    """Download WWDC sessions."""
    year = ctx.obj["year"]
    directory = ctx.obj["directory"]
    verbose = ctx.obj["verbose"]

    if not session and not topic:
        click.echo("Error: Please specify either --session or --topic", err=True)
        ctx.exit(1)

    if session and topic:
        click.echo(
            "Error: Please specify either --session or --topic, not both", err=True
        )
        ctx.exit(1)

    # Import here to avoid circular imports
    from .downloader import WWDCDownloader

    downloader = WWDCDownloader(year=year, output_dir=directory, verbose=verbose)

    if session:
        session_ids = [s.strip() for s in session.split(",")]
        click.echo(f"Downloading sessions: {', '.join(session_ids)}")
        downloader.download_sessions(session_ids, text_only=text_only, force=force)
    else:
        click.echo(f"Downloading topic: {topic}")
        downloader.download_topic(topic, text_only=text_only, force=force)


@cli.group()
def list():
    """List available topics and sessions."""
    pass


@list.command(name="topics")
@click.pass_context
def list_topics(ctx: click.Context) -> None:
    """Show all available topics."""
    year = ctx.obj["year"]

    # Import here to avoid circular imports
    from .parser import WWDCParser

    parser = WWDCParser(year=year)
    topics = parser.get_topics()

    click.echo(f"\nAvailable topics for WWDC {year}:")
    for topic in topics:
        click.echo(f"  - {topic}")


@list.command(name="sessions")
@click.option("-t", "--topic", required=True, help="Topic name")
@click.pass_context
def list_sessions(ctx: click.Context, topic: str) -> None:
    """Show sessions in a topic."""
    year = ctx.obj["year"]

    # Import here to avoid circular imports
    from .parser import WWDCParser

    parser = WWDCParser(year=year)
    sessions = parser.get_sessions_for_topic(topic)

    click.echo(f"\nSessions in topic '{topic}' for WWDC {year}:")
    for session in sessions:
        click.echo(f"  - {session['id']}: {session['title']}")


@cli.command()
@click.option("-s", "--session", help="Session ID(s) to summarize")
@click.option("-t", "--topic", help="Summarize all sessions in topic")
@click.option("--force", is_flag=True, help="Regenerate existing summaries")
@click.option("-m", "--model", default="gpt-4o-mini", help="LLM model to use")
@click.pass_context
def summarize(
    ctx: click.Context, session: Optional[str], topic: Optional[str], force: bool, model: str
) -> None:
    """Generate AI summaries for sessions."""
    import asyncio
    from rich.console import Console
    console = Console()
    
    year = ctx.obj["year"]
    directory = ctx.obj["directory"]
    verbose = ctx.obj["verbose"]

    if not session and not topic:
        click.echo("Error: Please specify either --session or --topic", err=True)
        ctx.exit(1)

    # Import here to avoid circular imports
    from .summarizer import LLMSummarizer, setup_llm_cli
    
    try:
        summarizer = LLMSummarizer(model=model, verbose=verbose)
    except RuntimeError:
        console.print("\n[yellow]LLM CLI not found. Would you like to set it up?[/yellow]")
        if click.confirm("Setup LLM CLI?"):
            asyncio.run(setup_llm_cli())
            summarizer = LLMSummarizer(model=model, verbose=verbose)
        else:
            return
    
    output_dir = Path(directory) / str(year)

    if session:
        # Summarize specific sessions
        session_ids = [s.strip() for s in session.split(",")]
        for session_id in session_ids:
            # Find session in directory structure
            found = False
            for topic_dir in output_dir.iterdir():
                if not topic_dir.is_dir():
                    continue
                for session_dir in topic_dir.iterdir():
                    if session_dir.is_dir() and session_id in session_dir.name:
                        content_file = session_dir / "content.md"
                        summary_file = session_dir / "summary.md"
                        if content_file.exists():
                            console.print(f"[blue]Summarizing session {session_id}...[/blue]")
                            asyncio.run(summarizer.summarize_session(content_file, summary_file))
                            found = True
                            break
                if found:
                    break
            if not found:
                console.print(f"[red]Session {session_id} not found in downloaded content[/red]")
    else:
        # Summarize topic(s)
        if topic.lower() == "all":
            asyncio.run(summarizer.batch_summarize(output_dir, force=force))
        else:
            topic_dir = output_dir / topic
            if topic_dir.exists():
                asyncio.run(summarizer.summarize_topic(topic_dir, force=force))
            else:
                console.print(f"[red]Topic directory not found: {topic}[/red]")


@cli.command()
@click.argument("keywords", nargs=-1, required=True)
@click.option("-a", "--all-years", is_flag=True, help="Search across all years")
@click.pass_context
def find(ctx: click.Context, keywords: tuple[str, ...], all_years: bool) -> None:
    """Find sessions by keyword and output paths for files-to-prompt."""
    import subprocess
    from pathlib import Path
    
    directory = ctx.obj["directory"]
    
    # Determine which directories to search
    if all_years:
        # Search all year directories
        search_dirs = [d for d in directory.iterdir() if d.is_dir() and d.name.isdigit()]
        if not search_dirs:
            # Silent exit - no matches
            return
    else:
        # Search specific year
        year = ctx.obj["year"]
        year_dir = directory / str(year)
        if not year_dir.exists():
            # Silent exit - no matches
            return
        search_dirs = [year_dir]
    
    # Collect all matching files
    all_matches = {}
    
    for search_dir in search_dirs:
        for keyword in keywords:
            # Use ripgrep for fast searching (case-insensitive by default)
            cmd = ["rg", "-i", "-l", keyword, str(search_dir)]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                files = result.stdout.strip().split("\n")
                
                # Filter for content.md files only
                content_files = [f for f in files if f.endswith("content.md") and f]
                
                for file_path in content_files:
                    if file_path not in all_matches:
                        all_matches[file_path] = set()
                    all_matches[file_path].add(keyword)
                    
            except subprocess.CalledProcessError:
                # No matches for this keyword in this directory
                continue
            except FileNotFoundError:
                # Print to stderr so it doesn't interfere with piping
                click.echo("Error: ripgrep (rg) not found. Install with: brew install ripgrep", err=True)
                ctx.exit(1)
    
    if not all_matches:
        # Silent exit - no output
        return
    
    # Sort by number of matching keywords (most relevant first), then by year (newest first)
    sorted_matches = sorted(
        all_matches.items(), 
        key=lambda x: (len(x[1]), -int(Path(x[0]).parts[-4])),  # parts[-4] is the year
        reverse=True
    )
    
    # Output file paths for piping
    for file_path, _ in sorted_matches:
        click.echo(file_path)


@cli.command(name="export-llm")
@click.option("-t", "--topic", required=True, help='Topic to export or "all"')
@click.option("-o", "--output", type=Path, help="Output file path")
@click.option("--consolidated", is_flag=True, help="Create single consolidated file")
@click.pass_context
def export_llm(ctx: click.Context, topic: str, output: Optional[Path], consolidated: bool) -> None:
    """Export LLM-ready content."""
    import asyncio
    from rich.console import Console
    console = Console()
    
    year = ctx.obj["year"]
    directory = ctx.obj["directory"]

    # Import here to avoid circular imports
    from .summarizer import LLMExporter

    year_dir = Path(directory) / str(year)
    exporter = LLMExporter()
    
    if consolidated:
        # Create single consolidated file
        output_file = output if output else year_dir.parent / f"wwdc-{year}-llm.txt"
        if topic.lower() == "all":
            asyncio.run(exporter.create_consolidated_export(year_dir, output_file))
        else:
            asyncio.run(exporter.create_consolidated_export(year_dir, output_file, [topic]))
    else:
        # Export individual topics
        if topic.lower() == "all":
            export_dir = output if output else year_dir.parent / "llm-exports"
            asyncio.run(exporter.export_all_topics(year_dir, export_dir))
        else:
            topic_dir = year_dir / topic
            if topic_dir.exists():
                output_file = output if output else year_dir.parent / f"{topic}-llm.txt"
                asyncio.run(exporter.export_topic_to_llm(topic_dir, output_file))
            else:
                console.print(f"[red]Topic directory not found: {topic}[/red]")


if __name__ == "__main__":
    cli()
