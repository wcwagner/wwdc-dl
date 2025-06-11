# WWDC-DL: Complete WWDC Content Downloader & Organizer

A Python command-line tool that downloads and organizes Apple WWDC (Worldwide Developers Conference) session content. It automatically extracts transcripts, code samples, chapter markers, and resource links from WWDC videos, organizing everything by topic for easy navigation and reference. Built for developers who want offline access to WWDC content or need to process it for AI/LLM training.

## Key Features

- **Smart Organization**: Automatically organizes sessions by Apple's official topics (Swift, SwiftUI, Developer Tools, etc.)
- **Rich Content Extraction**: Extracts transcripts with timestamps, code samples with context, chapter markers, and documentation links
- **Video Downloads**: Optional SD-quality video downloads for offline viewing
- **Metadata Caching**: Fast incremental updates with intelligent caching
- **AI-Ready Output**: Structured markdown format perfect for LLM training or AI processing

## Installation

```bash
# Clone the repository
git clone https://github.com/wwagner19/wwdc-dl
cd wwdc-dl

# Install using uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Usage

### Available Topics

The tool supports all official Apple Developer video topics:
- `accessibility-inclusion` - Accessibility & Inclusion
- `app-services` - App Services
- `app-store-distribution-marketing` - App Store, Distribution & Marketing
- `audio-video` - Audio & Video
- `business-education` - Business & Education
- `design` - Design
- `developer-tools` - Developer Tools (Xcode, Swift Assist, etc.)
- `essentials` - Essentials
- `graphics-games` - Graphics & Games
- `health-fitness` - Health & Fitness
- `machine-learning-ai` - Machine Learning & AI
- `maps-location` - Maps & Location
- `photos-camera` - Photos & Camera
- `privacy-security` - Privacy & Security
- `safari-web` - Safari & Web
- `spatial-computing` - Spatial Computing
- `swift` - Swift
- `swiftui-ui-frameworks` - SwiftUI & UI Frameworks
- `system-services` - System Services

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
wwdc-content/                            # Default output directory
└── 2025/
    ├── developer-tools/
    │   ├── 247-whats-new-xcode/
    │   │   ├── video.mp4                # SD quality video
    │   │   ├── content.md               # Transcript, code, metadata
    │   │   └── summary.md               # AI-generated summary
    │   └── 248-swift-assist/
    │       └── ...
    ├── swiftui-ui-frameworks/
    │   └── 280-code-along-cook-up/
    │       └── ...
    ├── machine-learning-ai/
    ├── accessibility-inclusion/
    └── metadata.json                    # Cache with sessions and topic mappings
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

### Key Improvements Completed

1. **Fixed topic detection** ✓ - Now uses Apple's official `/videos/[topic]/` endpoints to get accurate topic mappings
2. **Improved filename sanitization** ✓ - Removes apostrophes and special characters, keeps filenames short and clean
3. **Dynamic topic mapping** ✓ - Automatically builds session-to-topic mappings by scraping Apple's topic pages
4. **Better metadata caching** ✓ - Caches both session metadata and topic mappings for faster subsequent runs
5. **Fixed directory structure** ✓ - Sessions downloaded with `-t all` now go to their proper topic directories, not an "all" directory
6. **Enhanced content extraction** ✓ - Now properly extracts chapters with timestamps and resource links (documentation)
7. **Enriched metadata** ✓ - metadata.json now includes chapters, resources, and descriptions for each session

### Remaining Improvements

1. **Implement incremental logic** - Check existing files before downloading
2. **Add progress for topics** - Show overall progress when downloading topics
3. **Better error handling** - Retry failed downloads, handle missing content

### Development

This project uses `uv` for package management and running commands.

```bash
# Install dependencies
uv sync

# Run the CLI tool
uv run wwdc [command]

# Run tests
uv run pytest

# Type checking
uvx pyright

# Format code
uvx ruff format

# Lint and fix
uvx ruff check --fix

# Check without fixing
uvx ruff check
```

#### Pre-commit Hooks (Recommended)

To automatically format and lint code before commits:

```bash
# Install pre-commit
uvx pre-commit install

# Run manually on all files
uvx pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
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
# Using uv to run commands:

# 1. Download all developer tools sessions
uv run wwdc download -t developer-tools

# 2. Download specific sessions
uv run wwdc download -s 247,268,280

# 3. Download everything without videos
uv run wwdc download -t all --text-only

# 4. List available topics
uv run wwdc list topics

# 5. List sessions in a topic
uv run wwdc list sessions -t swift

# Future features (not yet implemented):
# Generate summaries
uv run wwdc summarize -t developer-tools

# Export for LLM training
uv run wwdc export-llm -t developer-tools -o developer-tools-2025.txt
```

## Important Notes for Development

- **Always use `uv run wwdc` to run the CLI tool**
- **Use `uvx` for development tools (ruff, pyright, etc.)**
- **Do NOT use `-v` flag - it's not implemented. The tool accepts `--verbose` in some places but not consistently**
- **Sessions are organized by topic directories, never in an "all" directory**