"""Parser for WWDC HTML content."""

import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup


class WWDCParser:
    """Parses WWDC website content."""

    BASE_URL = "https://developer.apple.com"

    def __init__(self, year: int):
        self.year = str(year)
        self._topics_cache: Optional[List[str]] = None
        self._sessions_cache: Dict[str, List[Dict]] = {}

    def get_topics(self) -> List[str]:
        """Get list of available topics (synchronous wrapper)."""
        import asyncio

        return asyncio.run(self._get_topics_async())

    def get_sessions_for_topic(self, topic: str) -> List[Dict]:
        """Get sessions for a specific topic (synchronous wrapper)."""
        import asyncio

        return asyncio.run(self._get_sessions_for_topic_async(topic))

    async def _get_topics_async(self) -> List[str]:
        """Get list of available topics from WWDC page."""
        if self._topics_cache:
            return self._topics_cache

        # Official Apple Developer video topic slugs
        topics = [
            "accessibility-inclusion",
            "app-services",
            "app-store-distribution-marketing",
            "audio-video",
            "business-education",
            "design",
            "developer-tools",
            "essentials",
            "graphics-games",
            "health-fitness",
            "machine-learning-ai",
            "maps-location",
            "photos-camera",
            "privacy-security",
            "safari-web",
            "spatial-computing",
            "swift",
            "swiftui-ui-frameworks",
            "system-services",
        ]

        self._topics_cache = topics
        return self._topics_cache

    async def _get_sessions_for_topic_async(
        self, topic: str, session: aiohttp.ClientSession = None
    ) -> List[Dict]:
        """Get sessions for a specific topic from Apple's topic page."""
        cache_key = f"{topic}_{self.year}"
        if cache_key in self._sessions_cache:
            return self._sessions_cache[cache_key]

        sessions = []
        topic_url = f"{self.BASE_URL}/videos/{topic}/"

        try:
            # Use provided session or create a temporary one
            if session:
                response = await session.get(topic_url)
            else:
                async with aiohttp.ClientSession() as temp_session:
                    response = await temp_session.get(topic_url)

            if response.status != 200:
                return sessions

            html = await response.text()
            soup = BeautifulSoup(html, "lxml")

            # Find all video links on the topic page
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # Match WWDC video links for any year
                match = re.match(r"/videos/play/wwdc(\d{4})/(\d+)/", href)
                if match:
                    year = match.group(1)
                    session_id = match.group(2)

                    # Get the title from the link text or nearby elements
                    title = ""
                    # Try to find title in the link's parent structure
                    parent = link.parent
                    while parent and not title:
                        h4 = parent.find("h4")
                        if h4:
                            title = h4.get_text(strip=True)
                            break
                        parent = parent.parent

                    if not title:
                        title = link.get_text(strip=True)

                    sessions.append(
                        {
                            "id": session_id,
                            "year": year,
                            "title": title,
                            "url": urljoin(self.BASE_URL, href),
                            "topic": topic,
                        }
                    )

        except Exception as e:
            print(f"Error fetching sessions for topic {topic}: {e}")

        self._sessions_cache[cache_key] = sessions
        return sessions

    async def get_all_sessions_async(
        self, session: aiohttp.ClientSession
    ) -> List[Dict]:
        """Get all sessions for the year with topic information."""
        all_sessions = []
        seen_sessions = set()

        # Build session-to-topic mapping first
        topic_mapping = await self.build_session_topic_mapping_async(session)

        # Get all topics
        topics = await self._get_topics_async()

        # Collect all sessions from each topic page
        for topic in topics:
            topic_sessions = await self._get_sessions_for_topic_async(topic, session)
            for sess in topic_sessions:
                if sess.get("year") == self.year and sess["id"] not in seen_sessions:
                    seen_sessions.add(sess["id"])
                    # Ensure topic is set
                    sess["topic"] = topic
                    all_sessions.append(sess)

        return all_sessions

    async def get_sessions_for_topic_async(
        self, topic: str, session: aiohttp.ClientSession
    ) -> List[Dict]:
        """Get sessions for a specific topic and filter by current year."""
        all_sessions = await self._get_sessions_for_topic_async(topic, session)
        # Filter to only return sessions from the current year
        return [s for s in all_sessions if s.get("year") == self.year]

    async def get_session_metadata_async(
        self, session_id: str, session: aiohttp.ClientSession
    ) -> Optional[Dict]:
        """Get metadata for a specific session."""
        url = f"{self.BASE_URL}/videos/play/wwdc{self.year}/{session_id}/"

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()

                # Extract video URLs
                video_urls = self._extract_video_urls(html, session_id)

                # Extract basic metadata
                soup = BeautifulSoup(html, "lxml")
                title = video_urls.get("title", "")

                if not title:
                    # Try to get title from meta tag
                    meta_title = soup.find("meta", {"property": "og:title"})
                    if meta_title:
                        title = meta_title.get("content", "")
                        # Clean up title
                        for suffix in [
                            f" - WWDC {self.year} - Apple Developer",
                            " - WWDC25 - Videos - Apple Developer",
                            " - Apple Developer",
                        ]:
                            title = title.replace(suffix, "")

                # Get topic from Apple's topic pages
                topic = await self.get_topic_for_session_async(session_id, session)

                return {
                    "id": session_id,
                    "title": title.strip(),
                    "url": url,
                    "video_urls": video_urls,
                    "topic": topic,
                }

        except Exception as e:
            print(f"Error fetching metadata for session {session_id}: {e}")
            return None

    async def parse_session_content_async(
        self, session_id: str, session: aiohttp.ClientSession
    ) -> Optional[Dict]:
        """Parse full content for a session including transcript and code."""
        url = f"{self.BASE_URL}/videos/play/wwdc{self.year}/{session_id}/"

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, "lxml")

                content = {
                    "description": self._extract_description(soup),
                    "chapters": self._extract_chapters(soup),
                    "resources": self._extract_resources(soup),
                    "code_samples": self._extract_code_samples(soup),
                    "transcript": self._extract_transcript(soup),
                }

                return content

        except Exception as e:
            print(f"Error parsing content for session {session_id}: {e}")
            return None

    def _extract_video_urls(
        self, html: str, session_id: str
    ) -> Dict[str, Optional[str]]:
        """Extract video URLs from HTML."""
        urls = {"hd": None, "sd": None, "hls": None, "title": None}

        # Extract title
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

        # Extract video URLs
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

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract session description."""
        # Look in details section
        details_section = soup.find("li", {"data-supplement-id": "details"})
        if details_section:
            desc_elem = details_section.find("p")
            if desc_elem:
                return desc_elem.get_text(strip=True)

        # Fallback to meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc:
            return meta_desc.get("content", "")

        return ""

    def _extract_chapters(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract chapter markers."""
        chapters = []

        # Find all links with time parameter
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "?time=" in href:
                # Extract parent li to get full text
                parent_li = link.find_parent("li")
                if parent_li:
                    li_text = parent_li.get_text(strip=True)
                    # Match pattern like "0:00 - Introduction" or "3:17 - Single-threaded code"
                    match = re.match(r"(\d+:\d+)\s*-\s*(.+)", li_text)
                    if match:
                        time_str = match.group(1)
                        chapter_name = match.group(2)

                        # Extract timestamp from URL
                        time_match = re.search(r"\?time=(\d+)", href)
                        timestamp = time_match.group(1) if time_match else ""

                        chapters.append(
                            {
                                "time": time_str,
                                "timestamp": timestamp,
                                "name": chapter_name,
                            }
                        )

        return chapters

    def _extract_resources(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract resource links."""
        resources = []
        seen_urls = set()

        # Find all links that look like documentation or resources
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Skip video download links and empty text
            if not text or "Video" in text or ".mp4" in href:
                continue

            # Look for documentation, guides, or other resources
            if any(
                keyword in href.lower() or keyword in text.lower()
                for keyword in [
                    "docs.swift.org",
                    "swift.org/migration",
                    "developer.apple.com/documentation",
                    "guide",
                    "documentation",
                    "reference",
                ]
            ):
                url = href if href.startswith("http") else urljoin(self.BASE_URL, href)

                # Avoid duplicates
                if url not in seen_urls and text:
                    seen_urls.add(url)
                    resources.append({"title": text, "url": url})

        return resources

    def _extract_code_samples(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract code samples."""
        code_samples = []

        # Find code supplement (try different selectors)
        code_section = soup.find("li", class_="supplement sample-code")
        if not code_section:
            code_section = soup.find("li", {"data-supplement-id": "sample-code"})
        if not code_section:
            code_section = soup.find("li", {"data-supplement-id": "code"})
        if not code_section:
            return code_samples

        # Find all code sample containers
        for container in code_section.find_all(
            "li", class_="sample-code-main-container"
        ):
            sample_data = {}

            # Extract title and timestamp from the jump-to-time link
            time_link = container.find("a", class_="jump-to-time-sample")
            if time_link:
                sample_data["title"] = time_link.get_text(strip=True)
                sample_data["timestamp"] = time_link.get("data-start-time", "")

                # Extract time display from parent p tag
                p_tag = time_link.parent
                if p_tag and p_tag.name == "p":
                    # Get all text nodes before the link
                    time_text = ""
                    for child in p_tag.children:
                        if child == time_link:
                            break
                        if isinstance(child, str):
                            time_text += child

                    # Clean up and extract time
                    time_text = time_text.strip()
                    if time_text.endswith(" -"):
                        time_text = time_text[:-2].strip()
                    sample_data["time_display"] = time_text
                else:
                    sample_data["time_display"] = ""

            # Extract code
            pre_elem = container.find("pre", class_="code-source")
            if pre_elem:
                code_elem = pre_elem.find("code")
                if code_elem:
                    # Get raw text content
                    code_text = code_elem.get_text()

                    # Clean up any HTML entities
                    import html

                    code_text = html.unescape(code_text)

                    sample_data["code"] = code_text

                    # Detect language (default to swift for WWDC)
                    sample_data["language"] = "swift"

            if "code" in sample_data and sample_data["code"].strip():
                code_samples.append(sample_data)

        return code_samples

    def _extract_transcript(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract transcript with timestamps."""
        transcript = []

        transcript_section = soup.find("section", id="transcript-content")
        if not transcript_section:
            return transcript

        for sentence in transcript_section.find_all("span", class_="sentence"):
            timestamp_elem = sentence.find("span", {"data-start": True})
            if timestamp_elem:
                timestamp = timestamp_elem.get("data-start", "")
                text = sentence.get_text(strip=True)
                if text:
                    transcript.append({"timestamp": timestamp, "text": text})

        return transcript

    async def get_topic_for_session_async(
        self, session_id: str, session: aiohttp.ClientSession
    ) -> Optional[str]:
        """Get the topic for a specific session by checking all topic pages."""
        # Check cache first
        if session_id in self._sessions_cache:
            return self._sessions_cache[session_id].get("topic")

        # Get all topics
        topics = await self._get_topics_async()

        # Check each topic page to find this session
        for topic in topics:
            sessions = await self._get_sessions_for_topic_async(topic, session)
            for session_info in sessions:
                if (
                    session_info.get("id") == session_id
                    and session_info.get("year") == self.year
                ):
                    # Cache the result
                    self._sessions_cache[session_id] = {"topic": topic}
                    return topic

        return None

    async def build_session_topic_mapping_async(
        self, session: aiohttp.ClientSession
    ) -> Dict[str, str]:
        """Build a complete mapping of session IDs to topics for the current year."""
        mapping = {}
        topics = await self._get_topics_async()

        print(f"Building session-to-topic mapping for WWDC {self.year}...")

        for topic in topics:
            sessions = await self._get_sessions_for_topic_async(topic, session)
            for session_info in sessions:
                if session_info.get("year") == self.year:
                    session_id = session_info.get("id")
                    if session_id:
                        mapping[session_id] = topic

        print(f"Found {len(mapping)} sessions across {len(topics)} topics")
        return mapping
