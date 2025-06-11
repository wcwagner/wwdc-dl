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
            
        # For now, return predefined topics
        # TODO: Parse from WWDC main page
        topics = [
            "developer-tools",
            "swiftui",
            "swift",
            "app-frameworks",
            "machine-learning",
            "accessibility",
            "audio-video",
            "business",
            "design",
            "distribution",
            "games",
            "health-fitness",
            "maps-location",
            "privacy-security",
            "safari-web",
            "system-frameworks",
        ]
        
        self._topics_cache = topics
        return topics
        
    async def _get_sessions_for_topic_async(self, topic: str) -> List[Dict]:
        """Get sessions for a specific topic."""
        if topic in self._sessions_cache:
            return self._sessions_cache[topic]
            
        # TODO: Implement actual parsing from topic pages
        # For now, return empty list
        sessions = []
        
        self._sessions_cache[topic] = sessions
        return sessions
        
    async def get_all_sessions_async(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get all sessions for the year."""
        all_sessions = []
        
        # Get sessions from the main videos page
        videos_url = f"{self.BASE_URL}/videos/wwdc{self.year}/"
        
        try:
            async with session.get(videos_url) as response:
                if response.status != 200:
                    return all_sessions
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Find all session links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Match pattern like /videos/play/wwdc2025/247/
                    match = re.match(rf'/videos/play/wwdc{self.year}/(\d+)/', href)
                    if match:
                        session_id = match.group(1)
                        title = link.get_text(strip=True)
                        
                        # Skip if it's just the session number
                        if title and title != session_id:
                            all_sessions.append({
                                'id': session_id,
                                'title': title,
                                'url': urljoin(self.BASE_URL, href)
                            })
                            
        except Exception as e:
            print(f"Error fetching all sessions: {e}")
            
        return all_sessions
        
    async def get_sessions_for_topic_async(self, topic: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Get sessions for a specific topic."""
        # For now, get all sessions and filter by topic
        # TODO: Implement proper topic-based filtering
        all_sessions = await self.get_all_sessions_async(session)
        return all_sessions
        
    async def get_session_metadata_async(self, session_id: str, session: aiohttp.ClientSession) -> Optional[Dict]:
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
                soup = BeautifulSoup(html, 'lxml')
                title = video_urls.get('title', '')
                
                if not title:
                    # Try to get title from meta tag
                    meta_title = soup.find('meta', {'property': 'og:title'})
                    if meta_title:
                        title = meta_title.get('content', '')
                        # Clean up title
                        for suffix in [
                            f" - WWDC {self.year} - Apple Developer",
                            " - WWDC25 - Videos - Apple Developer", 
                            " - Apple Developer"
                        ]:
                            title = title.replace(suffix, "")
                            
                return {
                    'id': session_id,
                    'title': title.strip(),
                    'url': url,
                    'video_urls': video_urls
                }
                
        except Exception as e:
            print(f"Error fetching metadata for session {session_id}: {e}")
            return None
            
    async def parse_session_content_async(self, session_id: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Parse full content for a session including transcript and code."""
        url = f"{self.BASE_URL}/videos/play/wwdc{self.year}/{session_id}/"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                content = {
                    'description': self._extract_description(soup),
                    'chapters': self._extract_chapters(soup),
                    'resources': self._extract_resources(soup),
                    'code_samples': self._extract_code_samples(soup),
                    'transcript': self._extract_transcript(soup)
                }
                
                return content
                
        except Exception as e:
            print(f"Error parsing content for session {session_id}: {e}")
            return None
            
    def _extract_video_urls(self, html: str, session_id: str) -> Dict[str, Optional[str]]:
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
        
        details_section = soup.find("li", {"data-supplement-id": "details"})
        if not details_section:
            return chapters
            
        chapter_list = details_section.find("ul", class_="chapter-list")
        if chapter_list:
            for chapter in chapter_list.find_all("li", class_="chapter-item"):
                timestamp = chapter.get("data-start-time", "")
                chapter_text = chapter.get_text(strip=True)
                if " - " in chapter_text:
                    time_str, name = chapter_text.split(" - ", 1)
                    chapters.append({
                        "time": time_str.strip(),
                        "timestamp": timestamp,
                        "name": name.strip(),
                    })
                    
        return chapters
        
    def _extract_resources(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract resource links."""
        resources = []
        
        details_section = soup.find("li", {"data-supplement-id": "details"})
        if not details_section:
            return resources
            
        resources_section = details_section.find("ul", class_="links small")
        if resources_section:
            for link in resources_section.find_all("a"):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if href and text:
                    url = href if href.startswith("http") else urljoin(self.BASE_URL, href)
                    resources.append({
                        "title": text,
                        "url": url
                    })
                    
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
        for container in code_section.find_all("li", class_="sample-code-main-container"):
            sample_data = {}
            
            # Extract title and timestamp from the jump-to-time link
            time_link = container.find("a", class_="jump-to-time-sample")
            if time_link:
                sample_data['title'] = time_link.get_text(strip=True)
                sample_data['timestamp'] = time_link.get("data-start-time", "")
                
                # Extract time display from parent p tag
                p_tag = time_link.parent
                if p_tag and p_tag.name == 'p':
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
                    sample_data['time_display'] = time_text
                else:
                    sample_data['time_display'] = ""
            
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
                    
                    sample_data['code'] = code_text
                    
                    # Detect language (default to swift for WWDC)
                    sample_data['language'] = 'swift'
                    
            if 'code' in sample_data and sample_data['code'].strip():
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
                    transcript.append({
                        "timestamp": timestamp,
                        "text": text
                    })
                    
        return transcript