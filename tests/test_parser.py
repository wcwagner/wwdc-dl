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
        
        # Check that code samples appear at the right timestamps
        code_sample_1_found = False
        code_sample_2_found = False
        
        for i in range(transcript_start, len(lines)):
            line = lines[i]
            
            # Check for first code sample (should appear after timestamp 70-80)
            if "[01:15]" in line and i + 1 < len(lines):
                # Next few lines should contain the code sample
                upcoming_lines = '\n'.join(lines[i:i+10])
                if "### Code Sample: TextEditor and String" in upcoming_lines:
                    code_sample_1_found = True
                    
            # Check for second code sample (should appear after timestamp 280)
            if "[04:43]" in line and i + 1 < len(lines):
                upcoming_lines = '\n'.join(lines[i:i+10])
                if "### Code Sample: AttributedString Basics" in upcoming_lines:
                    code_sample_2_found = True
        
        assert code_sample_1_found, "First code sample not found at correct position"
        assert code_sample_2_found, "Second code sample not found at correct position"