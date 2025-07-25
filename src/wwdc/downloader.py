"""WWDC content downloader with async support."""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import aiohttp
import yt_dlp
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)

from .parser import WWDCParser

console = Console()


class WWDCDownloader:
    """Handles downloading WWDC content with concurrent support."""

    def __init__(self, year: int, output_dir: Path, verbose: bool = False):
        self.year = str(year)
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.parser = WWDCParser(year=year)
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent downloads
        self._metadata_cache: Dict[str, dict] = {}
        self._topic_mapping: Dict[
            str, str
        ] = {}  # session_id -> topic, populated dynamically

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=1800, connect=30, sock_read=300)
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
            force_close=False,
            keepalive_timeout=30,
        )
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
        )
        await self._load_metadata_cache()

        # Build topic mapping if not cached
        if not self._topic_mapping and self.verbose:
            console.print("[yellow]Building session-to-topic mapping...[/yellow]")
            self._topic_mapping = await self.parser.build_session_topic_mapping_async(
                self.session
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _load_metadata_cache(self):
        """Load cached metadata if available."""
        cache_file = self.output_dir / self.year / "metadata.json"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                    self._metadata_cache = data.get("sessions", {})
                    self._topic_mapping = data.get("topic_mapping", {})
            except Exception:
                pass

    async def _save_metadata_cache(self):
        """Save metadata cache."""
        cache_file = self.output_dir / self.year / "metadata.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        data = {"sessions": self._metadata_cache, "topic_mapping": self._topic_mapping}

        async with aiofiles.open(cache_file, "w") as f:
            await f.write(json.dumps(data, indent=2))

    def download_sessions(
        self, session_ids: List[str], text_only: bool = False, force: bool = False
    ):
        """Download multiple sessions."""
        asyncio.run(self._download_sessions_async(session_ids, text_only, force))

    def download_topic(self, topic: str, text_only: bool = False, force: bool = False):
        """Download all sessions in a topic."""
        asyncio.run(self._download_topic_async(topic, text_only, force))

    async def _download_sessions_async(
        self, session_ids: List[str], text_only: bool, force: bool
    ):
        """Async implementation of session downloads."""
        async with self:
            tasks = []
            for session_id in session_ids:
                # Topic will be determined from metadata during download
                task = self._download_single_session(session_id, None, text_only, force)
                tasks.append(task)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                await asyncio.gather(*tasks)

            await self._save_metadata_cache()

    async def _download_topic_async(self, topic: str, text_only: bool, force: bool):
        """Async implementation of topic downloads."""
        async with self:
            # Get sessions for topic
            if topic.lower() == "all":
                sessions = await self.parser.get_all_sessions_async(self.session)
            else:
                sessions = await self.parser.get_sessions_for_topic_async(
                    topic, self.session
                )

            if not sessions:
                console.print(f"[red]No sessions found for topic: {topic}[/red]")
                return

            console.print(
                f"[green]Found {len(sessions)} sessions for topic: {topic}[/green]"
            )

            # Map sessions to topics
            for session in sessions:
                # Don't use "all" as a fallback topic
                if topic.lower() == "all":
                    self._topic_mapping[session["id"]] = session.get("topic", "general")
                else:
                    self._topic_mapping[session["id"]] = session.get("topic", topic)

            # Download sessions
            tasks = []
            for session in sessions:
                # For "all", use the session's actual topic, not "all"
                if topic.lower() == "all":
                    # When downloading all, use the session's topic (should never be None)
                    session_topic = session.get("topic")
                    if not session_topic:
                        console.print(
                            f"[red]Warning: Session {session['id']} has no topic![/red]"
                        )
                        session_topic = "unknown"
                else:
                    # For specific topics, use what we have or fall back to the requested topic
                    session_topic = session.get("topic", topic)

                if self.verbose:
                    console.print(
                        f"[yellow]Session {session['id']} topic: {session.get('topic')} -> using: {session_topic}[/yellow]"
                    )
                task = self._download_single_session(
                    session["id"], session_topic, text_only, force
                )
                tasks.append(task)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                await asyncio.gather(*tasks)

            await self._save_metadata_cache()

    async def _download_single_session(
        self, session_id: str, topic: Optional[str], text_only: bool, force: bool
    ):
        """Download a single session with all its content."""
        async with self.semaphore:
            try:
                # Get session metadata first to determine topic
                metadata = await self._get_session_metadata(session_id)
                if not metadata:
                    console.print(
                        f"[red]Failed to get metadata for session {session_id}[/red]"
                    )
                    return

                # Use topic from metadata if not provided
                if not topic and "topic" in metadata:
                    topic = metadata["topic"]
                    # Update our mapping cache
                    self._topic_mapping[session_id] = topic

                # Determine output directory based on topic
                if topic and topic != "general" and topic != "all":
                    session_dir = (
                        self.output_dir / self.year / self._sanitize_filename(topic)
                    )
                else:
                    session_dir = self.output_dir / self.year / "general"

                if self.verbose:
                    console.print(
                        f"[cyan]Session {session_id} -> directory: {session_dir}[/cyan]"
                    )

                session_dir.mkdir(parents=True, exist_ok=True)

                # Create session-specific directory
                session_title = metadata.get("title", f"session-{session_id}")
                safe_title = self._sanitize_filename(f"{session_id}-{session_title}")
                session_path = session_dir / safe_title
                session_path.mkdir(exist_ok=True)

                # Check if already downloaded
                content_file = session_path / "content.md"
                video_file = session_path / "video.mp4"

                if (
                    not force
                    and content_file.exists()
                    and (text_only or video_file.exists())
                ):
                    console.print(
                        f"[yellow]Session {session_id} already downloaded, skipping[/yellow]"
                    )
                    return

                # Download content
                console.print(
                    f"[blue]Downloading session {session_id}: {session_title}[/blue]"
                )

                # Download text content
                await self._download_text_content(session_id, metadata, session_path)

                # Download video if requested
                if not text_only:
                    await self._download_video(session_id, metadata, session_path)

                console.print(f"[green]✓ Completed session {session_id}[/green]")

            except Exception as e:
                console.print(f"[red]Error downloading session {session_id}: {e}[/red]")
                if self.verbose:
                    console.print_exception()

    async def _get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """Get session metadata from cache or fetch it."""
        if session_id in self._metadata_cache:
            return self._metadata_cache[session_id]

        metadata = await self.parser.get_session_metadata_async(
            session_id, self.session
        )
        if metadata:
            self._metadata_cache[session_id] = metadata

        return metadata

    async def _download_text_content(
        self, session_id: str, metadata: Dict, output_path: Path
    ):
        """Download and save text content (transcript, code, etc)."""
        content_file = output_path / "content.md"

        # Parse full content
        full_content = await self.parser.parse_session_content_async(
            session_id, self.session
        )
        if not full_content:
            console.print(
                f"[red]Failed to parse content for session {session_id}[/red]"
            )
            return

        # Update metadata cache with chapters and resources
        if session_id in self._metadata_cache:
            self._metadata_cache[session_id]["chapters"] = full_content.get(
                "chapters", []
            )
            self._metadata_cache[session_id]["resources"] = full_content.get(
                "resources", []
            )
            self._metadata_cache[session_id]["description"] = full_content.get(
                "description", ""
            )

        # Format content as markdown
        markdown_content = self._format_content_markdown(metadata, full_content)

        # Save content
        async with aiofiles.open(content_file, "w", encoding="utf-8") as f:
            await f.write(markdown_content)

    async def _download_video(self, session_id: str, metadata: Dict, output_path: Path):
        """Download video using yt-dlp."""
        video_file = output_path / "video.mp4"

        if video_file.exists():
            console.print(
                f"[yellow]Video already exists for session {session_id}[/yellow]"
            )
            return

        video_urls = metadata.get("video_urls", {})
        download_url = (
            video_urls.get("sd") or video_urls.get("hd") or video_urls.get("hls")
        )

        if not download_url:
            console.print(f"[red]No video URL found for session {session_id}[/red]")
            return

        # Use yt-dlp for download
        ydl_opts = {
            "outtmpl": str(video_file),
            "quiet": not self.verbose,
            "no_warnings": not self.verbose,
            "format": "best[height<=720]/best",  # Prefer SD quality
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await asyncio.get_event_loop().run_in_executor(
                    None, ydl.download, [download_url]
                )
        except Exception as e:
            console.print(
                f"[red]Failed to download video for session {session_id}: {e}[/red]"
            )

    def _format_content_markdown(self, metadata: Dict, content: Dict) -> str:
        """Format session content as markdown."""
        lines = []

        # Title and metadata
        title = metadata.get("title", "Unknown Session")
        session_id = metadata.get("id", "")

        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**Session {session_id}** - WWDC {self.year}")
        lines.append("")

        # Description
        if content.get("description"):
            lines.append("## Description")
            lines.append(content["description"])
            lines.append("")

        # Chapters
        if content.get("chapters"):
            lines.append("## Chapters")
            for chapter in content["chapters"]:
                lines.append(f"- {chapter['time']} - {chapter['name']}")
            lines.append("")

        # Resources
        if content.get("resources"):
            lines.append("## Resources")
            for resource in content["resources"]:
                lines.append(f"- [{resource['title']}]({resource['url']})")
            lines.append("")

        # Transcript with interleaved code samples
        if content.get("transcript") or content.get("code_samples"):
            lines.append("## Transcript")
            lines.append("")

            # Prepare code samples indexed by timestamp
            code_by_timestamp = {}
            if content.get("code_samples"):
                for sample in content["code_samples"]:
                    if sample.get("timestamp"):
                        timestamp = int(sample["timestamp"])
                        if timestamp not in code_by_timestamp:
                            code_by_timestamp[timestamp] = []
                        code_by_timestamp[timestamp].append(sample)

            # Process transcript entries
            if content.get("transcript"):
                for i, entry in enumerate(content["transcript"]):
                    entry_timestamp = entry.get("timestamp", "")

                    # Check if we need to insert code samples before this entry
                    if entry_timestamp:
                        try:
                            current_ts = int(float(entry_timestamp))

                            # Find code samples that should appear before this timestamp
                            for code_ts in sorted(code_by_timestamp.keys()):
                                if code_ts <= current_ts:
                                    # Insert code samples
                                    for sample in code_by_timestamp[code_ts]:
                                        lines.append("")
                                        time_display = sample.get(
                                            "time_display",
                                            self._format_timestamp(str(code_ts)),
                                        )
                                        title = sample.get("title", "Code Sample")
                                        lines.append(
                                            f"### Code Sample: {title} - [{time_display}]"
                                        )
                                        lines.append("")
                                        lines.append(
                                            "```" + sample.get("language", "swift")
                                        )
                                        lines.append(sample.get("code", "").rstrip())
                                        lines.append("```")
                                        lines.append("")

                                    # Remove processed samples
                                    del code_by_timestamp[code_ts]
                        except ValueError:
                            pass

                    # Add transcript text
                    formatted_time = (
                        self._format_timestamp(entry_timestamp)
                        if entry_timestamp
                        else ""
                    )
                    if formatted_time:
                        lines.append(f"[{formatted_time}] {entry.get('text', '')}")
                    else:
                        lines.append(entry.get("text", ""))

            # Add any remaining code samples at the end
            for code_ts in sorted(code_by_timestamp.keys()):
                for sample in code_by_timestamp[code_ts]:
                    lines.append("")
                    time_display = sample.get(
                        "time_display", self._format_timestamp(str(code_ts))
                    )
                    title = sample.get("title", "Code Sample")
                    lines.append(f"### Code Sample: {title} - [{time_display}]")
                    lines.append("")
                    lines.append("```" + sample.get("language", "swift"))
                    lines.append(sample.get("code", "").rstrip())
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)

    def _format_timestamp(self, seconds: str) -> str:
        """Format timestamp from seconds to MM:SS."""
        try:
            total_seconds = int(float(seconds))
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        except:
            return "00:00"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        import unicodedata

        # Normalize Unicode characters
        filename = unicodedata.normalize("NFKD", filename)

        # Convert to lowercase
        filename = filename.lower()

        # Remove apostrophes and quotes entirely (don't replace with hyphen)
        filename = re.sub(r"[''`''‛\"″‟''ʻʼ']", "", filename)

        # Replace spaces and remaining punctuation with hyphens
        filename = re.sub(
            r"[\s\-–—_]+", "-", filename
        )  # spaces, hyphens, dashes, underscores
        filename = re.sub(r"[,:;!?]+", "-", filename)  # punctuation marks

        # Remove other invalid filesystem characters
        filename = re.sub(r'[<>:"/\\|?*()[\]{}]+', "", filename)

        # Replace multiple hyphens with single hyphen
        filename = re.sub(r"-+", "-", filename)

        # Remove leading/trailing hyphens and dots
        filename = filename.strip("-. ")

        # Keep filenames reasonably short while preserving key info
        if len(filename) > 100:  # Reduced from 200 for better usability
            # Try to cut at a word boundary
            truncated = filename[:100]
            last_hyphen = truncated.rfind("-")
            if last_hyphen > 80:  # If there's a reasonable break point
                filename = truncated[:last_hyphen]
            else:
                filename = truncated

        return filename
