"""Command-line interface for wwdc."""

import click
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="wwdc")
@click.option("-y", "--year", type=int, default=datetime.now().year, help="WWDC year")
@click.option("-d", "--directory", type=Path, default=Path("./wwdc-content"), help="Output directory")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, year: int, directory: Path, verbose: bool) -> None:
    """WWDC toolkit - download, list, summarize, and export Apple Developer content."""
    ctx.ensure_object(dict)
    ctx.obj["year"] = year
    ctx.obj["directory"] = directory
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("-s", "--session", help="Session ID(s), comma-separated")
@click.option("-t", "--topic", help='Topic name or "all"')
@click.option("--text-only", is_flag=True, help="Skip video downloads")
@click.option("--force", is_flag=True, help="Re-download existing files")
@click.pass_context
def download(ctx: click.Context, session: Optional[str], topic: Optional[str], text_only: bool, force: bool) -> None:
    """Download WWDC sessions."""
    year = ctx.obj["year"]
    directory = ctx.obj["directory"]
    verbose = ctx.obj["verbose"]
    
    if not session and not topic:
        click.echo("Error: Please specify either --session or --topic", err=True)
        ctx.exit(1)
    
    if session and topic:
        click.echo("Error: Please specify either --session or --topic, not both", err=True)
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
@click.pass_context
def summarize(ctx: click.Context, session: Optional[str], topic: Optional[str], force: bool) -> None:
    """Generate AI summaries for sessions."""
    year = ctx.obj["year"]
    directory = ctx.obj["directory"]
    
    if not session and not topic:
        click.echo("Error: Please specify either --session or --topic", err=True)
        ctx.exit(1)
    
    # Import here to avoid circular imports
    from .summarizer import Summarizer
    
    summarizer = Summarizer(year=year, output_dir=directory)
    
    if session:
        session_ids = [s.strip() for s in session.split(",")]
        click.echo(f"Generating summaries for sessions: {', '.join(session_ids)}")
        summarizer.summarize_sessions(session_ids, force=force)
    else:
        click.echo(f"Generating summaries for topic: {topic}")
        summarizer.summarize_topic(topic, force=force)


@cli.command(name="export-llm")
@click.option("-t", "--topic", required=True, help='Topic to export or "all"')
@click.option("-o", "--output", type=Path, required=True, help="Output file path")
@click.pass_context
def export_llm(ctx: click.Context, topic: str, output: Path) -> None:
    """Export LLM-ready content."""
    year = ctx.obj["year"]
    directory = ctx.obj["directory"]
    
    # Import here to avoid circular imports
    from .exporter import LLMExporter
    
    exporter = LLMExporter(year=year, content_dir=directory)
    
    click.echo(f"Exporting {topic} to {output}")
    exporter.export(topic=topic, output_file=output)
    click.echo(f"Export complete: {output}")


if __name__ == "__main__":
    cli()