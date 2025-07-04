# Swift 6.2 Concurrency Documentation Crawling Project

## Project Goal

Create a comprehensive Swift 6.2 concurrency guide for macOS and iOS development by:
1. Crawling and converting modern Swift documentation to markdown
2. Focusing on concurrency patterns, migration strategies, and Swift 6.2 features
3. Building a consolidated guide that coding agents can use to implement modern idiomatic patterns

## Current State

### ✅ Completed
- Created directory structure in `docs/sources/`
- Created URL tracking file at `docs/crawled-urls.md`
- Created DOCC URL converter script at `docs/docc_url_converter.py` (renamed from apple_url_converter.py)
- Processed initial Swift.org pages:
  - Migration guide overview: `sources/swift-org/swift-6-migration-guide.md`
  - Data race safety: `sources/swift-org/data-race-safety.md`

### 🔄 In Progress
- Processing remaining Swift.org documentation pages
- Need to continue with Swift book concurrency chapter

### 📋 Remaining Tasks
1. Complete Swift.org documentation crawling
2. Process GitHub repository: LucasVanDongen/Modern-Concurrency-2025
3. Extract WWDC session transcripts (266, 268, 270 from 2025; 10170 from 2023)
4. Crawl community blog sources
5. Process Apple Developer documentation

## Directory Structure

```
docs/
├── sources/
│   ├── swift-org/      # Swift.org documentation
│   ├── apple-dev/      # Apple developer documentation
│   ├── blogs/          # Community blogs
│   ├── github/         # GitHub repositories
│   └── wwdc/           # WWDC session transcripts
├── crawled-urls.md     # Tracking all processed URLs
├── docc_url_converter.py # DOCC URL to JSON converter
└── CLAUDE.md           # This file - project instructions
```

## Key Instructions

### DOCC Archive Handling

Both Swift.org and Apple Developer documentation use DOCC format. These require conversion to JSON for processing.

#### URL Conversion Patterns

1. **Swift.org**: Replace `/documentation/` with `/data/documentation/` and append `.json`
   - Original: `https://www.swift.org/migration/documentation/migrationguide/`
   - JSON: `https://www.swift.org/migration/data/documentation/migrationguide.json`

2. **Apple Developer**: Replace `/documentation/` with `/tutorials/data/documentation/` and append `.json`
   - Original: `https://developer.apple.com/documentation/swift/updating_an_app_to_use_swift_concurrency`
   - JSON: `https://developer.apple.com/tutorials/data/documentation/swift/updating_an_app_to_use_swift_concurrency.json`

3. **Swift Book**: Replace `/documentation/` with `/data/documentation/` and append `.json`
   - Original: `https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/`
   - JSON: `https://docs.swift.org/swift-book/data/documentation/the-swift-programming-language/concurrency.json`

#### Processing DOCC JSON

Use the `llm` tool for DOCC to markdown conversion:

```bash
# Basic conversion
curl -s "https://www.swift.org/migration/data/documentation/migrationguide.json" | llm -m gemini-2.0-flash-latest -s "Convert this DocC archive to markdown" > output.md

# Detailed conversion with all content
curl -s "[json-url]" | llm -m gemini-2.0-flash-latest -s "Convert this DocC archive to markdown. Include all code examples with Swift syntax highlighting, important notes, warnings, and preserve the document structure." > output.md
```

### Processing Other Content

For HTML pages (blogs, articles):
```bash
# Convert HTML to markdown
curl -s "https://www.avanderlee.com/concurrency/async-await/" | llm -m gemini-2.0-flash-latest -s "Convert this HTML to markdown preserving all code examples and technical details"
```

For complex analysis across multiple files:
```bash
# Use gemini -p for analysis
gemini -p "@sources/ What are the key concurrency patterns in Swift 6.2?"
```

### WWDC Session Processing

For WWDC sessions, we'll keep everything self-contained in this docs directory:
1. Visit the WWDC video pages directly
2. Extract transcripts and relevant content manually or via web scraping
3. Convert to markdown and save in `sources/wwdc/` directory

Sessions to process:
- https://developer.apple.com/videos/play/wwdc2025/266/
- https://developer.apple.com/videos/play/wwdc2025/268/
- https://developer.apple.com/videos/play/wwdc2025/270/
- https://developer.apple.com/videos/play/wwdc2023/10170/

## Source URLs

### Swift.org Documentation
- Migration Guide: https://www.swift.org/migration/documentation/migrationguide/
- Swift Book Concurrency: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/

### Swift.org Migration Guide Sub-pages
- Data Race Safety: /dataracesafety
- Migration Strategy: /migrationstrategy
- Enabling Complete Checking: /completechecking
- Swift 6 Mode: /swift6mode
- Common Problems: /commonproblems
- Incremental Adoption: /incrementaladoption
- Source Compatibility: /sourcecompatibility
- Library Evolution: /libraryevolution

### Apple Developer
- Updating to Swift Concurrency: https://developer.apple.com/documentation/swift/updating_an_app_to_use_swift_concurrency

### Community Sources
- https://www.avanderlee.com/category/concurrency/
- https://www.donnywals.com/the-blog/
- https://www.hackingwithswift.com/articles/277/whats-new-in-swift-6-2
- https://github.com/LucasVanDongen/Modern-Concurrency-2025

### WWDC Videos
- https://developer.apple.com/videos/play/wwdc2025/266/
- https://developer.apple.com/videos/play/wwdc2025/268/
- https://developer.apple.com/videos/play/wwdc2025/270/
- https://developer.apple.com/videos/play/wwdc2023/10170/

## Important Notes

1. **DO NOT use Playwright** for DOCC-based documentation - use JSON endpoints
2. **Always update** `crawled-urls.md` after processing each URL
3. **Focus on** Swift 6.2 features, iOS 18+ APIs, and migration patterns
4. **Preserve all content** during initial crawl - summarization comes later
5. **Use uv** for Python scripts - see docc_url_converter.py for example

## Quick Start Commands

```bash
# Make URL converter executable
chmod +x docc_url_converter.py

# Convert a DOCC URL to JSON
./docc_url_converter.py [url]

# Process a DOCC page
curl -s "[json-url]" | llm -m gemini-2.0-flash-latest -s "Convert this DocC archive to markdown" > output.md

# Check progress
cat crawled-urls.md
```

## Next Steps When Resuming

1. Continue processing Swift.org migration guide sub-pages
2. Process the Swift book concurrency chapter
3. Clone and process the GitHub repository
4. Extract WWDC transcripts
5. Crawl community blog posts
6. Process Apple Developer documentation

The goal is lossless markdown conversion first, then consolidation and analysis in a later phase.