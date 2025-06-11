"""Command-line interface for wwdc."""

import click
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="wwdc")
@click.option("-y", "--year", type=int, default=datetime.now().year, help="WWDC year")
@click.option(
    "-d",
    "--directory",
    type=Path,
    default=Path("./wwdc-content"),
    help="Output directory",
)
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


@cli.command(name="extract-frames")
@click.option("-s", "--session", help="Session ID(s) to extract frames from")
@click.option("-t", "--topic", help="Topic to extract frames from")
@click.option("--method", default="smart", type=click.Choice(["smart", "keyframes", "interval"]), help="Frame extraction method")
@click.option("--advanced", is_flag=True, help="Use advanced content detection (requires extra dependencies)")
@click.pass_context
def extract_frames(ctx: click.Context, session: Optional[str], topic: Optional[str], method: str, advanced: bool) -> None:
    """Extract meaningful frames from videos."""
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
    from .frame_extractor import FrameExtractor, AdvancedFrameExtractor
    
    output_dir = Path(directory) / str(year)
    
    if advanced:
        extractor = AdvancedFrameExtractor(verbose=verbose)
        if not extractor.pyscenedetect_available:
            console.print("[yellow]PySceneDetect not available. Install with: pip install scenedetect[/yellow]")
        if not extractor.opencv_available:
            console.print("[yellow]OpenCV not available. Install with: pip install opencv-python[/yellow]")
    else:
        extractor = FrameExtractor(verbose=verbose)
    
    if session:
        # Extract frames from specific sessions
        session_ids = [s.strip() for s in session.split(",")]
        for session_id in session_ids:
            # Find session in directory structure
            found = False
            for topic_dir in output_dir.iterdir():
                if not topic_dir.is_dir():
                    continue
                for session_dir in topic_dir.iterdir():
                    if session_dir.is_dir() and session_id in session_dir.name:
                        video_file = session_dir / "video.mp4"
                        if video_file.exists():
                            frames_dir = session_dir / "frames"
                            console.print(f"[blue]Extracting frames from session {session_id}...[/blue]")
                            asyncio.run(extractor.extract_frames(video_file, frames_dir, method))
                            found = True
                            break
                if found:
                    break
            if not found:
                console.print(f"[red]Video not found for session {session_id}[/red]")
    else:
        # Extract frames from topic
        topic_dir = output_dir / topic
        if topic_dir.exists():
            asyncio.run(extractor.extract_frames_for_topic(topic_dir, method))
        else:
            console.print(f"[red]Topic directory not found: {topic}[/red]")


if __name__ == "__main__":
    cli()
