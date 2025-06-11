# WWDC: Complete Toolkit for Apple Developer Content

A Python command-line tool for managing WWDC content - download, list, summarize, and export sessions for LLM consumption. Downloads videos (SD quality), transcripts, code samples, and metadata, then generates AI summaries for creating LLMs.txt files.

## Overview

WWDC tool downloads and organizes WWDC content to help fast-forward LLM knowledge with the latest Apple development practices. It handles:
- Video downloads (SD quality for efficiency)
- Transcript and code extraction
- Smart incremental updates
- AI-powered summarization

## Installation

```bash
# Install from source
git clone https://github.com/wwagner19/wwdc
cd wwdc
pip install -e .
```

## Usage

### Basic Commands

```bash
# Download a specific session
wwdc download -s 247

# Download multiple sessions
wwdc download -s 247,248,249

# Download all sessions for a topic
wwdc download -t developer-tools

# Download everything
wwdc download -t all

# Download only text content (no videos)
wwdc download -s 247 --text-only

# List available topics
wwdc list topics

# List sessions in a topic
wwdc list sessions -t developer-tools

# Generate AI summary for a session
wwdc summarize -s 247

# Generate summaries for a whole topic
wwdc summarize -t developer-tools

# Export LLM-ready content
wwdc export-llm -t developer-tools -o developer-tools.txt
```

### Options

```
Global:
  -y, --year       WWDC year (default: 2025)
  -d, --directory  Output directory (default: ./wwdc-content)
  -v, --verbose    Enable verbose output

download:
  -s, --session    Session ID(s), comma-separated
  -t, --topic      Topic name or "all"
  --text-only      Skip video downloads
  --force          Re-download existing files

list:
  topics           Show all available topics
  sessions         Show sessions in a topic

summarize:
  -s, --session    Session ID(s) to summarize
  -t, --topic      Summarize all sessions in topic
  --force          Regenerate existing summaries

export-llm:
  -t, --topic      Topic to export or "all"
  -o, --output     Output file path
```

## Directory Structure

```
wwdc-content/                    # Default output directory
└── 2025/
    ├── developer-tools/
    │   ├── 247-whats-new-xcode/
    │   │   ├── video.mp4        # SD quality video
    │   │   ├── content.md       # Transcript, code, metadata
    │   │   └── summary.md       # AI-generated summary
    │   └── 248-swift-assist/
    │       └── ...
    ├── swiftui/
    │   └── ...
    └── metadata.json            # Cache of session information
```

## Content Files

### content.md
Contains the raw extracted content:
```markdown
# Session Title

**Session 247** - WWDC 2025

## Description
[Official description]

## Chapters
- 00:00 - Introduction
- 02:30 - New Features
- ...

## Resources
- [Documentation](...)
- [Sample Code](...)

## Code Samples

### Sample 1 - [02:30]
```swift
// Code here
```

## Transcript
[00:00] Welcome to What's New in Xcode...
```

### summary.md
AI-generated summary following the template from the prompt:
```markdown
# Session Title - Summary

## Session Info
Number, title, presenter. One sentence about what's new.

## Context
2-4 sentences explaining the problem and when you need these features.

## Requirements
iOS/macOS version requirements and mandatory changes.

## New APIs
[Structured API documentation with examples]

## Key Points
- Must-know items
- Important method names
- Common pitfalls
```

## Project Structure

```
wwdc/
├── src/
│   └── wwdcl_dl/
│       ├── __init__.py
│       ├── __main__.py         # Entry point
│       ├── cli.py              # Click CLI definitions
│       ├── downloader.py       # Download logic
│       ├── parser.py           # HTML parsing
│       ├── summarizer.py       # AI summaries
│       └── exporter.py         # LLM export logic
├── tests/
│   ├── __init__.py
│   ├── test_downloader.py
│   └── test_parser.py
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Implementation Details

### Core Components

**cli.py** - Command-line interface
```python
# Click-based CLI with commands: download, list, summarize, export-llm
# Minimal arguments, smart defaults
```

**downloader.py** - Async download management
```python
# Enhanced from provided code
# - Fixed concurrent downloads (5 workers)
# - SD-only video downloads
# - Smart incremental updates
# - Organized by topic directories
```

**parser.py** - Content extraction
```python
# Extract from WWDC pages:
# - Session metadata
# - Transcripts with timestamps
# - Code samples with context
# - Chapter markers
# - Resource links
```

**summarizer.py** - AI summary generation
```python
# Generate summaries using OpenAI/Anthropic
# Follow the provided template
# Batch processing for topics
# Cache summaries alongside content
```

**exporter.py** - LLM export
```python
# Combine summaries into LLMs.txt
# Group by topic or year
# Include migration guides
# Format for optimal LLM consumption
```

### Key Improvements Needed

1. **Fix code extraction** - Current parser misses some code blocks
2. **Add topic detection** - Parse WWDC topic pages to get session lists
3. **Implement incremental logic** - Check existing files before downloading
4. **Add progress for topics** - Show overall progress when downloading topics
5. **Better error handling** - Retry failed downloads, handle missing content

### Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Type check
pyright

# Format
ruff format

# Lint
ruff check --fix
```

## Roadmap

### Phase 1: Core Functionality ✓
- [ ] Basic video downloading
- [ ] Transcript extraction
- [ ] Fix code sample parsing
- [ ] Add topic-based organization
- [ ] Implement incremental downloads

### Phase 2: Summarization
- [ ] Integrate AI summarization
- [ ] Implement summary template
- [ ] Batch processing for topics
- [ ] Cache management

### Phase 3: LLM Export
- [ ] Combine summaries
- [ ] Format for LLM consumption
- [ ] Generate topic-specific files
- [ ] Include cross-references

## Design Principles

1. **Simple** - One command to download everything you need
2. **Smart** - Never re-download completed content
3. **Organized** - Clear directory structure by year/topic/session
4. **Efficient** - SD video, 5 concurrent downloads
5. **LLM-Ready** - Content formatted for AI consumption

## Example Workflow

```bash
# 1. Download all developer tools sessions
wwdc download -t developer-tools

# 2. Generate summaries
wwdc summarize -t developer-tools

# 3. Export for LLM training
wwdc export-llm -t developer-tools -o developer-tools-2025.txt

# Or do it all for the entire conference
wwdc download -t all
wwdc summarize -t all
wwdc export-llm -t all -o wwdc-2025-complete.txt
```