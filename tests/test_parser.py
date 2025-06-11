"""Tests for WWDC HTML parser."""

import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from wwdc.parser import WWDCParser


class TestCodeExtraction:
    """Test code sample extraction from WWDC HTML."""
    
    def test_extract_code_samples_session_280(self):
        """Test extracting code samples from session 280 HTML."""
        # Load test HTML
        test_file = Path(__file__).parent / "280-code-along-cook-up-a-rich-text-experience.html"
        with open(test_file, "r", encoding="utf-8") as f:
            html = f.read()
        
        soup = BeautifulSoup(html, 'lxml')
        parser = WWDCParser(year=2025)
        
        # Extract code samples
        code_samples = parser._extract_code_samples(soup)
        
        # Verify we got all code samples
        assert len(code_samples) >= 20, f"Expected at least 20 code samples, got {len(code_samples)}"
        
        # Check first sample
        first_sample = code_samples[0]
        assert first_sample['title'] == "TextEditor and String"
        assert first_sample['timestamp'] == "75"
        assert first_sample['time_display'] == "1:15"
        assert "import SwiftUI" in first_sample['code']
        assert "struct RecipeEditor: View" in first_sample['code']
        
        # Check another sample with more complex title
        basics_sample = next((s for s in code_samples if "initial attempt" in s['title']), None)
        assert basics_sample is not None
        assert basics_sample['title'] == "Build custom controls: Basics (initial attempt)"
        assert "@State private var selection" in basics_sample['code']
        
        # Verify code is properly cleaned (no HTML entities)
        for sample in code_samples:
            assert "&quot;" not in sample['code']
            assert "&#x27;" not in sample['code']
            assert "&lt;" not in sample['code']
            assert "&gt;" not in sample['code']
            
        # Verify timestamps are numeric strings
        for sample in code_samples:
            assert sample['timestamp'].isdigit(), f"Timestamp should be numeric: {sample['timestamp']}"
            
    def test_format_code_samples_in_markdown(self):
        """Test formatting code samples in markdown output."""
        parser = WWDCParser(year=2025)
        
        # Mock code samples
        code_samples = [
            {
                'title': 'TextEditor and String',
                'timestamp': '75',
                'time_display': '1:15',
                'code': 'import SwiftUI\n\nstruct RecipeEditor: View {\n    @Binding var text: String\n}',
                'language': 'swift'
            },
            {
                'title': 'AttributedString Basics',
                'timestamp': '283',
                'time_display': '4:43',
                'code': 'var text = AttributedString("Hello")',
                'language': 'swift'
            }
        ]
        
        # Format content
        content = {
            'description': 'Test description',
            'chapters': [],
            'resources': [],
            'code_samples': code_samples,
            'transcript': [
                {'timestamp': '0', 'text': 'Welcome to the session.'},
                {'timestamp': '70', 'text': 'Let me show you a TextEditor example.'},
                {'timestamp': '80', 'text': 'This is how it works.'},
                {'timestamp': '280', 'text': 'Now let\'s look at AttributedString.'},
                {'timestamp': '290', 'text': 'It\'s very powerful.'}
            ]
        }
        
        metadata = {'title': 'Test Session', 'id': '280'}
        
        # Create a mock downloader instance to test formatting
        from wwdc.downloader import WWDCDownloader
        downloader = WWDCDownloader(year=2025, output_dir=Path('.'))
        markdown = downloader._format_content_markdown(metadata, content)
        
        # Verify code samples are interleaved with transcript
        lines = markdown.split('\n')
        
        # Find transcript section
        transcript_start = next(i for i, line in enumerate(lines) if line == "## Transcript")
        
        # Check that code samples appear in the transcript section
        transcript_section = '\n'.join(lines[transcript_start:])
        
        # Check that both code samples are present
        assert "### Code Sample: TextEditor and String - [1:15]" in transcript_section, "First code sample not found"
        assert "### Code Sample: AttributedString Basics - [4:43]" in transcript_section, "Second code sample not found"
        
        # Verify code samples appear before their related transcript entries
        # Find positions of code samples and related transcript entries
        code1_pos = transcript_section.find("### Code Sample: TextEditor and String")
        code2_pos = transcript_section.find("### Code Sample: AttributedString Basics")
        trans1_pos = transcript_section.find("[01:20] This is how it works.")
        trans2_pos = transcript_section.find("[04:50] It's very powerful.")
        
        # Code samples should appear somewhere in the transcript
        assert code1_pos >= 0, "First code sample not in transcript"
        assert code2_pos >= 0, "Second code sample not in transcript"
        
        # Second code sample should appear after the first
        assert code2_pos > code1_pos, "Code samples not in correct order"


class TestTopicMapping:
    """Test topic mapping from Apple's website."""
    
    def test_get_topics(self):
        """Test getting list of available topics."""
        parser = WWDCParser(year=2025)
        
        # Get topics synchronously
        topics = parser.get_topics()
        
        # Verify we have the expected topics
        assert "developer-tools" in topics
        assert "swift" in topics
        assert "swiftui-ui-frameworks" in topics
        assert "accessibility-inclusion" in topics
        assert "machine-learning-ai" in topics
        
        # Verify all topics follow the expected slug format
        for topic in topics:
            assert topic.islower(), f"Topic '{topic}' should be lowercase"
            assert ' ' not in topic, f"Topic '{topic}' should not contain spaces"
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from wwdc.downloader import WWDCDownloader
        downloader = WWDCDownloader(year=2025, output_dir=Path('.'))
        
        test_cases = [
            # (input, expected)
            ("What's new in Xcode", "whats-new-in-xcode"),
            ("Swift Assist: Your AI companion", "swift-assist-your-ai-companion"),
            ("Building \"great\" apps", "building-great-apps"),
            ("Code-along: Cook up a rich experience!", "code-along-cook-up-a-rich-experience"),
            ("Spaces   and---multiple---hyphens", "spaces-and-multiple-hyphens"),
            ("Special chars: <>/\\|?*", "special-chars"),
            ("Apostrophe's and quotes' test", "apostrophes-and-quotes-test"),
            ("UPPERCASE TO lowercase", "uppercase-to-lowercase"),
            # Test filename truncation (100 char limit, cut at word boundary)
            ("Very " + "long " * 30 + "filename", "very" + "-long" * 19),  # Will truncate at 100 chars
        ]
        
        for input_str, expected in test_cases:
            result = downloader._sanitize_filename(input_str)
            assert result == expected, f"Expected '{expected}' for '{input_str}', got '{result}'"
            # Ensure it's valid for filesystem
            assert not any(c in result for c in '<>:"/\\|?*'), f"Invalid chars in result: {result}"
            assert len(result) <= 100, f"Result too long: {len(result)} chars"