# WWDC-DL

A command-line tool for downloading, organizing, and searching Apple WWDC session content. Downloads transcripts, code samples, and optionally videos from WWDC sessions, organizing them in a central cache for easy access and search.

## Features

- Download WWDC session content (transcripts, code samples, videos)
- Search across all sessions by keyword
- Organized by topic and year in `~/.wwdc`
- Generate AI summaries using LLM CLI
- Export content for LLM training

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

## Quick Start

```bash
# Download a specific session
uv run wwdc download -s 247

# Download all sessions for a topic (text only)
uv run wwdc download -t swiftui --text-only

# Search for content across all sessions
uv run wwdc find 'NavigationStack' | files-to-prompt

# Search across all years
uv run wwdc find 'App Intents' --all-years | files-to-prompt
```

## Commands

### `download` - Download WWDC content
```bash
# Download specific sessions
wwdc download -s 247,248,249

# Download entire topic
wwdc download -t developer-tools

# Download all content (text only)
wwdc download -t all --text-only

# Force re-download
wwdc download -s 247 --force
```

### `find` - Search sessions by keyword
```bash
# Search in current year (2025)
wwdc find 'ShowSnippetView' 'snippet'

# Search in specific year
wwdc -y 2024 find 'NavigationStack'

# Search across all downloaded years
wwdc find 'App Intents' --all-years

# Pipe to files-to-prompt for LLM context
wwdc find 'perform()' 'AppIntent' | files-to-prompt
```

### `list` - Browse available content
```bash
# List all topics
wwdc list topics

# List sessions in a topic
wwdc list sessions -t swift
```

### `summarize` - Generate AI summaries (requires LLM CLI)
```bash
# Summarize specific sessions
wwdc summarize -s 247,248

# Summarize entire topic
wwdc summarize -t developer-tools

# Use specific model
wwdc summarize -s 247 -m gpt-4o-mini
```

### `export-llm` - Export for LLM training
```bash
# Export topic summaries
wwdc export-llm -t developer-tools -o devtools.txt

# Export all summaries
wwdc export-llm -t all --consolidated -o wwdc-2025.txt
```

## Options

- `-y, --year` - Specify WWDC year (default: current year)
- `-v, --verbose` - Enable verbose output

## Content Structure

All content is stored in `~/.wwdc/`:

```
~/.wwdc/
└── 2025/
    ├── developer-tools/
    │   └── 247-whats-new-xcode/
    │       ├── content.md    # Transcript & code samples
    │       ├── summary.md    # AI-generated summary
    │       └── video.mp4     # Optional video
    └── metadata.json         # Session metadata cache
```

## Requirements

- Python 3.8+
- ripgrep (`brew install ripgrep`)
- Optional: LLM CLI for summaries (`pip install llm`)
- Optional: files-to-prompt (`pip install files-to-prompt`)

## License

MIT License - See LICENSE file for details.