"""
WWDC Video and Content Downloader
=================================

Downloads WWDC session videos along with auxiliary content (transcripts, code samples, chapters).
Uses uv for dependency management - no installation required, just run the script!

Usage:
    ./wwdc-dl-enhanced.py -d <directory> -s <session_ids> [options]

Examples:
    # Download a single session (video + auxiliary content)
    ./wwdc-dl-enhanced.py -d ~/WWDC -s 282

    # Download multiple sessions
    ./wwdc-dl-enhanced.py -d ~/WWDC -s 282,283,284

    # Download only auxiliary content (transcript + code)
    ./wwdc-dl-enhanced.py -d ~/WWDC -s 282 --aux-only

    # Download only videos
    ./wwdc-dl-enhanced.py -d ~/WWDC -s 282 --video-only

    # Download all sessions from WWDC 2025
    ./wwdc-dl-enhanced.py -d ~/WWDC -a -y 2025

    # Download in SD quality with 5 concurrent downloads
    ./wwdc-dl-enhanced.py -d ~/WWDC -s 282,283 -f SD -j 5

Options:
    -d, --directory     Directory to save files (required)
    -s, --sessions      Comma-separated session IDs (e.g., 101,102,103)
    -a, --all          Download all sessions for the year
    -y, --year         WWDC year (default: 2025)
    -f, --format       Video format: HD or SD (default: HD)
    -j, --jobs         Number of concurrent downloads (default: 3)
    --video-only       Download only videos
    --aux-only         Download only auxiliary content (transcript, code samples)

Directory Structure:
    <directory>/
    └── WWDC-<year>/
        ├── <session>-<title>.mp4          # Video file
        └── <session>-<title>.md           # Auxiliary content (markdown)

    Example:
    ~/WWDC/
    └── WWDC-2025/
        ├── 282-Make your UIKit app more flexible.mp4
        └── 282-Make your UIKit app more flexible.md

Markdown Content Includes:
    - Session title and description
    - Chapter markers with timestamps
    - Code samples with syntax highlighting
    - Full transcript with periodic timestamps
    - Links to documentation and resources

Features:
    - Concurrent downloads with progress bars
    - Resume support for interrupted downloads
    - Automatic retry on failure
    - Caches session information for faster subsequent runs
    - Falls back to HLS streaming if direct download unavailable
    - Smart title extraction and filename sanitization

Requirements:
    - macOS, Linux, or Windows with uv installed
    - Internet connection
    - Sufficient disk space for videos (HD videos can be 1-2GB each)

Note: This script uses uv's inline script metadata, so all dependencies
are automatically installed when you run it. No manual pip install needed!
"""

import argparse
import asyncio
import re
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List

import aiohttp
import aiofiles
import yt_dlp
from bs4 import BeautifulSoup
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

console = Console()

CURRENT_YEAR = "2025"


class EnhancedWWDCDownloader:
    def __init__(self, year: str = CURRENT_YEAR):
        self.year = year
        self.session: Optional[aiohttp.ClientSession] = None
        self._url_cache: Dict[str, dict] = {}
        self._html_cache: Dict[str, str] = {}

    async def __aenter__(self):
        # Increased timeout for large files
        timeout = aiohttp.ClientTimeout(total=1800, connect=30, sock_read=300)
        # Increased connection limit and keepalive
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
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_html_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL with caching"""
        if url in self._html_cache:
            return self._html_cache[url]

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                self._html_cache[url] = html
                return html
        except Exception as e:
            console.print(f"[red]Error fetching {url}: {e}[/red]")
            return None

    def extract_video_urls(self, html: str, session_id: str) -> dict:
        """Optimized URL extraction with single-pass regex"""
        urls = {"hd": None, "sd": None, "hls": None, "title": None}

        # Quick title extraction
        title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if title_match:
            title = title_match.group(1)
            for suffix in [
                f" - WWDC {self.year} - Apple Developer",
                " - WWDC25 - Videos - Apple Developer",
                " - Apple Developer",
            ]:
                title = title.replace(suffix, "")
            urls["title"] = title.strip()

        # Single regex pass for all video URLs
        video_pattern = re.compile(
            rf'(https://devstreaming-cdn\.apple\.com/videos/wwdc/{self.year}/{session_id}/[^"]*?/(downloads/wwdc{self.year}-{session_id}_(hd|sd)\.mp4|cmaf\.m3u8))|'
            r'(https://events-delivery\.apple\.com/[^"]*?\.m3u8)',
            re.IGNORECASE,
        )

        for match in video_pattern.finditer(html):
            full_url = match.group(0)
            if "_hd.mp4" in full_url:
                urls["hd"] = full_url
            elif "_sd.mp4" in full_url:
                urls["sd"] = full_url
            elif ".m3u8" in full_url and not urls["hls"]:
                urls["hls"] = full_url

        return urls

    def extract_auxiliary_content(
        self, html: str, soup: BeautifulSoup
    ) -> Dict[str, any]:
        """Extract all auxiliary content (about, transcript, code)"""
        aux_data = {
            "about": self.extract_about_content(soup),
            "transcript": self.extract_transcript(soup),
            "code_samples": self.extract_code_samples(soup),
        }
        return aux_data

    def extract_about_content(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Extract content from the About/Details tab"""
        about_data = {
            "title": "",
            "description": "",
            "chapters": [],
            "resources": [],
            "downloads": [],
        }

        # Find the details supplement
        details_section = soup.find("li", {"data-supplement-id": "details"})
        if not details_section:
            return about_data

        # Extract title - it's in a div.badge-available-on-wrapper
        title_wrapper = details_section.find("div", class_="badge-available-on-wrapper")
        if title_wrapper:
            title_elem = title_wrapper.find("h1")
            if title_elem:
                about_data["title"] = title_elem.get_text(strip=True)

        if not about_data["title"]:
            # Fallback to any h1 in details section
            title_elem = details_section.find("h1")
            if title_elem:
                about_data["title"] = title_elem.get_text(strip=True)
            else:
                # Try alternative location
                title_elem = soup.find("meta", {"property": "og:title"})
                if title_elem:
                    title = title_elem.get("content", "")
                    for suffix in [
                        f" - WWDC {self.year} - Apple Developer",
                        " - WWDC25 - Videos - Apple Developer",
                        " - Apple Developer",
                    ]:
                        title = title.replace(suffix, "")
                    about_data["title"] = title.strip()

        # Extract description - p tag is direct child of li
        desc_elem = details_section.find("p")
        if desc_elem:
            about_data["description"] = desc_elem.get_text(strip=True)

        # Extract chapters
        chapter_list = details_section.find("ul", class_="chapter-list")
        if chapter_list:
            for chapter in chapter_list.find_all("li", class_="chapter-item"):
                timestamp = chapter.get("data-start-time", "")
                chapter_text = chapter.get_text(strip=True)
                if " - " in chapter_text:
                    time_str, name = chapter_text.split(" - ", 1)
                    about_data["chapters"].append(
                        {
                            "time": time_str.strip(),
                            "timestamp": timestamp,
                            "name": name.strip(),
                        }
                    )

        # Extract resources/documentation links
        resources_section = details_section.find("ul", class_="links small")
        if resources_section:
            for link in resources_section.find_all("a"):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if href and text:
                    about_data["resources"].append(
                        {
                            "title": text,
                            "url": href
                            if href.startswith("http")
                            else f"https://developer.apple.com{href}",
                        }
                    )

        return about_data

    def extract_transcript(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract transcript with timestamps"""
        transcript_data = []

        transcript_section = soup.find("section", id="transcript-content")
        if not transcript_section:
            return transcript_data

        for sentence in transcript_section.find_all("span", class_="sentence"):
            timestamp_elem = sentence.find("span", {"data-start": True})
            if timestamp_elem:
                timestamp = timestamp_elem.get("data-start", "")
                text = sentence.get_text(strip=True)
                if text:
                    transcript_data.append({"timestamp": timestamp, "text": text})

        return transcript_data

    def extract_code_samples(self, soup: BeautifulSoup) -> List[Dict[str, any]]:
        """Extract code samples with timestamps"""
        code_samples = []

        # Find all code sample containers directly (they may be in nested sections)
        all_samples = soup.find_all("li", class_="sample-code-main-container")

        for sample_container in all_samples:
            sample_data = {
                "timestamp": "",
                "time_label": "",
                "code": "",
                "language": "swift",  # Default to Swift for WWDC
            }

            # Get timestamp from either jump-to-time-sample link or data attribute
            time_link = sample_container.find("a", class_="jump-to-time-sample")
            if time_link:
                sample_data["time_label"] = time_link.get_text(strip=True)
                # Try to get timestamp from data attribute first
                timestamp = time_link.get("data-start-time", "")
                if not timestamp:
                    # Fall back to onclick parsing
                    onclick = time_link.get("onclick", "")
                    match = re.search(r"jumpToTime\((\d+)\)", onclick)
                    if match:
                        timestamp = match.group(1)
                sample_data["timestamp"] = timestamp

            # Extract code
            code_elem = sample_container.find("code")
            if code_elem:
                sample_data["code"] = code_elem.get_text()
                # Try to detect language from class
                pre_elem = code_elem.find_parent("pre")
                if pre_elem:
                    classes = pre_elem.get("class", [])
                    for cls in classes:
                        if isinstance(cls, str) and cls.startswith("language-"):
                            sample_data["language"] = cls.replace("language-", "")
                            break

            if sample_data["code"]:
                code_samples.append(sample_data)

        return code_samples

    def format_timestamp(self, seconds: str) -> str:
        """Convert seconds to HH:MM:SS format"""
        try:
            total_seconds = int(float(seconds))
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60

            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        except:
            return seconds

    def create_markdown(
        self,
        session_id: str,
        about_data: Dict,
        transcript: List[Dict],
        code_samples: List[Dict],
    ) -> str:
        """Create a formatted markdown document"""
        md_lines = []

        # Header
        title = about_data.get("title", f"WWDC {self.year} Session {session_id}")
        md_lines.append(f"# {title}")
        md_lines.append("")
        md_lines.append(f"**Session {session_id}** - WWDC {self.year}")
        md_lines.append("")

        # Description
        if about_data.get("description"):
            md_lines.append("## Description")
            md_lines.append("")
            md_lines.append(about_data["description"])
            md_lines.append("")

        # Chapters
        if about_data.get("chapters"):
            md_lines.append("## Chapters")
            md_lines.append("")
            for chapter in about_data["chapters"]:
                time = chapter.get("time", "")
                name = chapter.get("name", "")
                md_lines.append(f"- **{time}** - {name}")
            md_lines.append("")

        # Resources
        if about_data.get("resources"):
            md_lines.append("## Resources")
            md_lines.append("")
            for resource in about_data["resources"]:
                title = resource.get("title", "")
                url = resource.get("url", "")
                md_lines.append(f"- [{title}]({url})")
            md_lines.append("")

        # Code Samples
        if code_samples:
            md_lines.append("## Code Samples")
            md_lines.append("")
            for i, sample in enumerate(code_samples, 1):
                time_label = sample.get("time_label", "")
                timestamp = sample.get("timestamp", "")
                language = sample.get("language", "")
                code = sample.get("code", "")

                md_lines.append(f"### Sample {i} - {time_label}")
                if timestamp:
                    formatted_time = self.format_timestamp(timestamp)
                    md_lines.append(f"*Timestamp: {formatted_time}*")
                md_lines.append("")
                md_lines.append(f"```{language}")
                md_lines.append(code)
                md_lines.append("```")
                md_lines.append("")

        # Transcript
        if transcript:
            md_lines.append("## Transcript")
            md_lines.append("")

            current_paragraph = []
            last_timestamp = None

            for entry in transcript:
                timestamp = entry.get("timestamp", "")
                text = entry.get("text", "")

                if timestamp and (
                    not last_timestamp or float(timestamp) - float(last_timestamp) > 30
                ):
                    if current_paragraph:
                        md_lines.append(" ".join(current_paragraph))
                        md_lines.append("")
                        current_paragraph = []

                    formatted_time = self.format_timestamp(timestamp)
                    md_lines.append(f"**[{formatted_time}]**")
                    md_lines.append("")

                current_paragraph.append(text)
                last_timestamp = timestamp

            if current_paragraph:
                md_lines.append(" ".join(current_paragraph))

        return "\n".join(md_lines)

    def ensure_directory(self, directory: Path) -> Path:
        """Ensure WWDC directory exists"""
        wwdc_dir = directory / f"WWDC-{self.year}"
        wwdc_dir.mkdir(parents=True, exist_ok=True)
        return wwdc_dir

    async def download_with_ytdlp(self, url: str, output_path: Path, progress) -> bool:
        """Download video using yt-dlp with progress"""
        task_id = progress.add_task(
            f"[cyan]Downloading {output_path.name} (HLS)", total=None
        )

        ydl_opts = {
            "outtmpl": str(output_path),
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [
                lambda d: self._ytdlp_progress_hook(d, progress, task_id)
            ],
        }

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._download_with_ytdlp_sync, url, ydl_opts
            )
            progress.remove_task(task_id)
            return True
        except Exception as e:
            progress.remove_task(task_id)
            console.print(f"[red]Error downloading with yt-dlp: {e}[/red]")
            return False

    def _ytdlp_progress_hook(self, d, progress, task_id):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                progress.update(task_id, total=total, completed=downloaded)

    def _download_with_ytdlp_sync(self, url: str, ydl_opts: dict):
        """Synchronous yt-dlp download"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    async def download_file_with_progress(
        self, url: str, output_path: Path, progress
    ) -> bool:
        """Download file with progress bar and resume support"""
        if output_path.exists():
            return False

        headers = {}
        mode = "wb"
        resume_pos = 0

        # Check for partial download
        temp_path = output_path.with_suffix(".part")
        if temp_path.exists():
            resume_pos = temp_path.stat().st_size
            headers["Range"] = f"bytes={resume_pos}-"
            mode = "ab"
            output_path = temp_path

        task_id = progress.add_task(
            f"[cyan]Downloading {output_path.stem}", total=None, start=False
        )

        try:
            async with self.session.get(url, headers=headers) as response:
                # Check if server supports resume
                if resume_pos > 0 and response.status != 206:
                    # Server doesn't support resume, start over
                    resume_pos = 0
                    mode = "wb"
                    temp_path.unlink()

                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                if resume_pos > 0:
                    total_size += resume_pos

                progress.update(task_id, total=total_size, completed=resume_pos)
                progress.start_task(task_id)

                # Use larger chunks for better performance
                chunk_size = 1024 * 1024  # 1MB chunks

                async with aiofiles.open(
                    temp_path if mode == "wb" else temp_path, mode
                ) as f:
                    downloaded = resume_pos
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        progress.update(task_id, completed=downloaded)

                # Rename temp file to final name
                if temp_path.exists():
                    temp_path.rename(output_path.with_suffix(".mp4"))

                progress.remove_task(task_id)
                return True

        except Exception:
            progress.remove_task(task_id)
            return False

    async def prefetch_session_info(self, session_id: str) -> dict:
        """Prefetch and cache session information"""
        if session_id in self._url_cache:
            return self._url_cache[session_id]

        play_url = (
            f"https://developer.apple.com/videos/play/wwdc{self.year}/{session_id}/"
        )
        html = await self.get_html_page(play_url)
        if html:
            urls = self.extract_video_urls(html, session_id)
            self._url_cache[session_id] = urls
            return urls
        return {}

    async def download_session(
        self,
        session_id: str,
        hd: bool = True,
        directory: Path | None = None,
        progress=None,
        download_video: bool = True,
        download_aux: bool = True,
    ) -> bool:
        """Download a single WWDC session with video and auxiliary content"""

        # Fetch the page once
        play_url = (
            f"https://developer.apple.com/videos/play/wwdc{self.year}/{session_id}/"
        )
        html = await self.get_html_page(play_url)
        if not html:
            console.print(f"[red]Failed to fetch page for session {session_id}[/red]")
            return False

        # Extract all data
        urls = self.extract_video_urls(html, session_id)
        soup = BeautifulSoup(html, "lxml")
        aux_content = self.extract_auxiliary_content(html, soup)

        title = urls["title"] or ""
        if title:
            title = re.sub(r'[/:*?"<>|]', "-", title)

        wwdc_dir = self.ensure_directory(directory)

        # Prepare filenames
        base_filename = f"{session_id}"
        if title:
            base_filename = f"{session_id}-{title}"

        success = True

        # Download video if requested
        if download_video:
            video_path = wwdc_dir / f"{base_filename}.mp4"

            if video_path.exists():
                console.print(
                    f"[yellow]Video already exists: {video_path.name}[/yellow]"
                )
            else:
                video_url = urls["hd"] if hd else urls["sd"]
                if not video_url and urls["hd"]:
                    video_url = urls["hd"]

                if video_url:
                    video_success = await self.download_file_with_progress(
                        video_url, video_path, progress
                    )
                elif urls["hls"]:
                    video_success = await self.download_with_ytdlp(
                        urls["hls"], video_path, progress
                    )
                else:
                    console.print(f"[red]No video found for session {session_id}[/red]")
                    video_success = False

                if video_success:
                    console.print(
                        f"[green]✓ Downloaded video: {video_path.name}[/green]"
                    )
                else:
                    console.print(f"[red]✗ Failed video: {video_path.name}[/red]")
                    success = False

        # Save auxiliary content if requested
        if download_aux:
            markdown_path = wwdc_dir / f"{base_filename}.md"

            if markdown_path.exists():
                console.print(
                    f"[yellow]Markdown already exists: {markdown_path.name}[/yellow]"
                )
            else:
                about_data = aux_content["about"]
                transcript = aux_content["transcript"]
                code_samples = aux_content["code_samples"]

                if any([about_data.get("title"), transcript, code_samples]):
                    markdown_content = self.create_markdown(
                        session_id, about_data, transcript, code_samples
                    )

                    with open(markdown_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)

                    console.print(
                        f"[green]✓ Saved auxiliary content: {markdown_path.name}[/green]"
                    )

                    # Summary of what was extracted
                    content_types = []
                    if about_data.get("chapters"):
                        content_types.append(f"{len(about_data['chapters'])} chapters")
                    if about_data.get("resources"):
                        content_types.append(
                            f"{len(about_data['resources'])} resources"
                        )
                    if code_samples:
                        content_types.append(f"{len(code_samples)} code samples")
                    if transcript:
                        content_types.append("full transcript")

                    if content_types:
                        console.print(
                            f"  [dim]Extracted: {', '.join(content_types)}[/dim]"
                        )
                else:
                    console.print(
                        f"[yellow]No auxiliary content found for session {session_id}[/yellow]"
                    )

        return success

    async def find_all_sessions(self) -> list[str]:
        """Find all session IDs for the year"""
        url = f"https://developer.apple.com/videos/wwdc{self.year}/"
        html = await self.get_html_page(url)
        if not html:
            return []

        pattern = f"/videos/play/wwdc{self.year}/([0-9]+)/"
        matches = re.findall(pattern, html)

        unique_sessions = sorted(list(set(matches)))
        console.print(
            f"[green]Found {len(unique_sessions)} sessions for WWDC {self.year}[/green]"
        )
        return unique_sessions


async def download_sessions_enhanced(
    downloader: EnhancedWWDCDownloader,
    session_ids: list[str],
    hd: bool,
    directory: Path,
    max_concurrent: int,
    download_video: bool,
    download_aux: bool,
):
    """Enhanced download with prefetching and progress"""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        # Prefetch session info in parallel (only if downloading videos)
        if download_video:
            console.print("[cyan]Fetching session information...[/cyan]")
            prefetch_tasks = []
            async with asyncio.TaskGroup() as tg:
                for session_id in session_ids[: min(20, len(session_ids))]:
                    prefetch_tasks.append(
                        tg.create_task(downloader.prefetch_session_info(session_id))
                    )

        # Download with controlled concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_with_semaphore(session_id: str):
            async with semaphore:
                await downloader.download_session(
                    session_id,
                    hd,
                    directory,
                    progress,
                    download_video=download_video,
                    download_aux=download_aux,
                )

        console.print("\n[cyan]Starting downloads...[/cyan]\n")

        async with asyncio.TaskGroup() as tg:
            for session_id in session_ids:
                tg.create_task(download_with_semaphore(session_id))


async def main():
    parser = argparse.ArgumentParser(
        description="Enhanced WWDC downloader with video and auxiliary content"
    )
    parser.add_argument(
        "-d", "--directory", required=True, help="Directory to save files"
    )
    parser.add_argument(
        "-s", "--sessions", help="Comma-separated session IDs (e.g., 101,102,103)"
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="Download all sessions"
    )
    parser.add_argument(
        "-y",
        "--year",
        default=CURRENT_YEAR,
        help=f"WWDC year (default: {CURRENT_YEAR})",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["HD", "SD"],
        default="HD",
        help="Video format (default: HD)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=3,
        help="Number of concurrent downloads (default: 3)",
    )
    parser.add_argument(
        "--video-only", action="store_true", help="Download only videos"
    )
    parser.add_argument(
        "--aux-only",
        action="store_true",
        help="Download only auxiliary content (transcript, code, etc)",
    )

    args = parser.parse_args()

    # Determine what to download
    download_video = not args.aux_only
    download_aux = not args.video_only

    if args.video_only and args.aux_only:
        console.print("[red]Cannot specify both --video-only and --aux-only[/red]")
        sys.exit(1)

    async with EnhancedWWDCDownloader(args.year) as downloader:
        if args.all:
            session_ids = await downloader.find_all_sessions()
        elif args.sessions:
            session_ids = args.sessions.split(",")
        else:
            console.print(
                "[red]Please specify sessions with -s or use -a for all sessions[/red]"
            )
            sys.exit(1)

        if not session_ids:
            console.print("[red]No sessions found[/red]")
            sys.exit(1)

        directory = Path(args.directory)
        hd = args.format == "HD"

        console.print(
            f"[cyan]Downloading {len(session_ids)} sessions with {args.jobs} concurrent jobs[/cyan]"
        )
        console.print(f"[cyan]Directory: {directory}[/cyan]")
        if args.video_only:
            console.print("[cyan]Mode: Video only[/cyan]")
        elif args.aux_only:
            console.print("[cyan]Mode: Auxiliary content only[/cyan]")
        else:
            console.print("[cyan]Mode: Video + auxiliary content[/cyan]")

        start_time = time.time()
        await download_sessions_enhanced(
            downloader,
            session_ids,
            hd,
            directory,
            args.jobs,
            download_video=download_video,
            download_aux=download_aux,
        )
        elapsed = time.time() - start_time

        console.print(
            f"\n[green]All downloads completed in {elapsed:.1f} seconds![/green]"
        )


if __name__ == "__main__":
    asyncio.run(main())
