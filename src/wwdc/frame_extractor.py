"""Intelligent frame extraction from WWDC videos."""

import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console

console = Console()


class FrameExtractor:
    """Extract meaningful frames from WWDC videos using scene detection."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        # Optimal thresholds for WWDC presentations based on research
        self.scene_threshold = 0.35  # Balanced for presentations
        self.keyframe_only = True  # Use I-frames for efficiency
        self.quality = 2  # High quality (1-5, lower is better)

    async def extract_frames(
        self, video_path: Path, output_dir: Path, method: str = "smart"
    ) -> List[Dict]:
        """Extract frames from video using specified method.

        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            method: Extraction method ('smart', 'keyframes', 'interval')

        Returns:
            List of extracted frame metadata
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        if method == "smart":
            return await self._extract_smart_frames(video_path, output_dir)
        elif method == "keyframes":
            return await self._extract_keyframes(video_path, output_dir)
        elif method == "interval":
            return await self._extract_interval_frames(video_path, output_dir)
        else:
            raise ValueError(f"Unknown extraction method: {method}")

    async def _extract_smart_frames(
        self, video_path: Path, output_dir: Path
    ) -> List[Dict]:
        """Extract frames using intelligent scene detection."""
        console.print(f"[blue]Extracting frames using scene detection...[/blue]")

        # Build FFmpeg command for scene detection with keyframes
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"select='eq(pict_type,I)*gt(scene,{self.scene_threshold})',showinfo",
            "-vsync", "vfr",
            "-q:v", str(self.quality),
            "-f", "image2",
            str(output_dir / "frame_%05d.png"),
        ]

        # Run FFmpeg and capture output for timestamps
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        # Parse timestamps from FFmpeg output
        frames = self._parse_ffmpeg_output(stderr.decode())

        if self.verbose:
            console.print(f"[green]Extracted {len(frames)} frames[/green]")

        return frames

    async def _extract_keyframes(self, video_path: Path, output_dir: Path) -> List[Dict]:
        """Extract only keyframes (I-frames) from video."""
        console.print(f"[blue]Extracting keyframes...[/blue]")

        cmd = [
            "ffmpeg",
            "-skip_frame", "nokey",
            "-i", str(video_path),
            "-vsync", "vfr",
            "-frame_pts", "true",
            "-q:v", str(self.quality),
            str(output_dir / "frame_%05d.png"),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        # Get frame count
        frame_files = sorted(output_dir.glob("frame_*.png"))
        frames = []
        for i, frame_file in enumerate(frame_files):
            frames.append({
                "index": i,
                "filename": frame_file.name,
                "timestamp": None,  # Would need additional processing
            })

        return frames

    async def _extract_interval_frames(
        self, video_path: Path, output_dir: Path, interval: int = 30
    ) -> List[Dict]:
        """Extract frames at fixed intervals."""
        console.print(f"[blue]Extracting frames every {interval} seconds...[/blue]")

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"fps=1/{interval},select='gt(scene,0.2)'",
            "-vsync", "vfr",
            "-q:v", str(self.quality),
            str(output_dir / "frame_%05d.png"),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await process.communicate()

        # Get frame count
        frame_files = sorted(output_dir.glob("frame_*.png"))
        frames = []
        for i, frame_file in enumerate(frame_files):
            frames.append({
                "index": i,
                "filename": frame_file.name,
                "timestamp": i * interval,
            })

        return frames

    def _parse_ffmpeg_output(self, output: str) -> List[Dict]:
        """Parse FFmpeg showinfo output to extract frame metadata."""
        frames = []
        frame_pattern = re.compile(
            r"n:\s*(\d+)\s+pts:\s*(\d+)\s+pts_time:([\d.]+)"
        )

        for line in output.split('\n'):
            if 'showinfo' in line:
                match = frame_pattern.search(line)
                if match:
                    frame_num = int(match.group(1))
                    pts_time = float(match.group(3))
                    
                    frames.append({
                        "index": frame_num,
                        "filename": f"frame_{frame_num+1:05d}.png",
                        "timestamp": pts_time,
                        "time_str": self._format_timestamp(pts_time),
                    })

        return frames

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    async def extract_frames_for_topic(
        self, topic_dir: Path, method: str = "smart"
    ) -> Dict[str, List[Dict]]:
        """Extract frames for all videos in a topic directory."""
        results = {}
        
        for session_dir in topic_dir.iterdir():
            if not session_dir.is_dir():
                continue
                
            video_file = session_dir / "video.mp4"
            if not video_file.exists():
                continue
                
            frames_dir = session_dir / "frames"
            if frames_dir.exists() and list(frames_dir.glob("*.png")):
                console.print(f"[yellow]Frames already extracted for {session_dir.name}[/yellow]")
                continue
                
            console.print(f"[blue]Processing {session_dir.name}...[/blue]")
            frames = await self.extract_frames(video_file, frames_dir, method)
            results[session_dir.name] = frames
            
            # Save frame metadata
            metadata_file = frames_dir / "metadata.json"
            async with asyncio.Lock():
                with open(metadata_file, 'w') as f:
                    json.dump(frames, f, indent=2)
        
        return results


class AdvancedFrameExtractor(FrameExtractor):
    """Advanced frame extraction with content detection."""

    def __init__(self, verbose: bool = False):
        super().__init__(verbose)
        self.pyscenedetect_available = self._check_pyscenedetect()
        self.opencv_available = self._check_opencv()

    def _check_pyscenedetect(self) -> bool:
        """Check if PySceneDetect is available."""
        try:
            import scenedetect
            return True
        except ImportError:
            return False

    def _check_opencv(self) -> bool:
        """Check if OpenCV is available."""
        try:
            import cv2
            return True
        except ImportError:
            return False

    async def extract_with_content_detection(
        self, video_path: Path, output_dir: Path
    ) -> List[Dict]:
        """Extract frames with content-aware detection."""
        if self.pyscenedetect_available:
            return await self._extract_with_pyscenedetect(video_path, output_dir)
        else:
            console.print("[yellow]PySceneDetect not available, using FFmpeg[/yellow]")
            return await self._extract_smart_frames(video_path, output_dir)

    async def _extract_with_pyscenedetect(
        self, video_path: Path, output_dir: Path
    ) -> List[Dict]:
        """Use PySceneDetect for advanced scene detection."""
        from scenedetect import detect, ContentDetector, split_video_ffmpeg

        console.print("[blue]Using PySceneDetect for advanced detection...[/blue]")

        # Detect scenes
        scene_list = detect(str(video_path), ContentDetector(threshold=27.0))

        frames = []
        for i, (start, end) in enumerate(scene_list):
            # Extract representative frame from each scene
            timestamp = start.get_seconds()
            
            cmd = [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-frames:v", "1",
                "-q:v", str(self.quality),
                str(output_dir / f"frame_{i+1:05d}.png"),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await process.communicate()

            frames.append({
                "index": i,
                "filename": f"frame_{i+1:05d}.png",
                "timestamp": timestamp,
                "time_str": self._format_timestamp(timestamp),
                "scene_start": start.get_seconds(),
                "scene_end": end.get_seconds(),
            })

        return frames

    async def detect_code_frames(
        self, frames_dir: Path
    ) -> List[str]:
        """Detect frames containing code using OCR."""
        if not self.opencv_available:
            console.print("[yellow]OpenCV not available for code detection[/yellow]")
            return []

        try:
            import pytesseract
            import cv2
            import numpy as np
        except ImportError:
            console.print("[yellow]Tesseract not available for OCR[/yellow]")
            return []

        code_frames = []
        code_indicators = ['{', '}', '()', 'func', 'var', 'let', 'import', 'class', 'struct', '->']

        for frame_file in sorted(frames_dir.glob("frame_*.png")):
            # Read image
            img = cv2.imread(str(frame_file))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Check blur
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            if laplacian.var() < 100:  # Too blurry
                continue

            # OCR
            try:
                text = pytesseract.image_to_string(gray, config='--psm 6')
                if any(indicator in text for indicator in code_indicators):
                    code_frames.append(frame_file.name)
            except Exception:
                pass

        return code_frames