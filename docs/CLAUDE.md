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
- Created DOCC URL converter script at `docs/docc_url_converter.py`
- Processed Swift.org migration guide pages (all sub-pages)
- Processed Swift book concurrency chapter
- Processed Apple Developer concurrency guide
- Processed community blog posts (Hacking with Swift, Antoine van der Lee)
- Processed GitHub repository: LucasVanDongen/Modern-Concurrency-2025
- Processed all 4 WWDC sessions:
  - WWDC 2025 Session 266 - Explore concurrency in SwiftUI
  - WWDC 2025 Session 268 - Embracing Swift concurrency
  - WWDC 2025 Session 270 - Code-along: Elevate an app with Swift concurrency
  - WWDC 2023 Session 10170 - Beyond the basics of structured concurrency

### 📋 Remaining Tasks
1. Process additional community blog sources if needed
2. Consolidate and analyze all content for comprehensive guide

## Directory Structure

```
docs/
├── sources/
│   ├── swift-org/      # Swift.org documentation
│   ├── apple-dev/      # Apple developer documentation
│   ├── blogs/          # Community blogs
│   ├── github/         # GitHub repositories
│   └── wwdc/           # WWDC session transcripts
├── prompts/            # LLM prompts for conversions
│   ├── wwdc-session.prompt.md     # WWDC session conversion
│   ├── docc-archive.prompt.md     # DOCC archive conversion
│   ├── html-to-markdown.prompt.md # HTML to markdown conversion
│   └── restructure-wwdc.prompt.md # Restructure WWDC sessions
├── crawled-urls.md     # Tracking all processed URLs
├── docc_url_converter.py # DOCC URL to JSON converter
└── CLAUDE.md           # This file - project instructions
```

## Key Instructions

### Using Prompts

All LLM prompts are stored in the `prompts/` directory for version control and consistency:
- **wwdc-session.prompt.md** - Convert WWDC session HTML to markdown with proper formatting
- **docc-archive.prompt.md** - Convert DOCC JSON archives to markdown
- **html-to-markdown.prompt.md** - Convert general HTML pages to markdown
- **restructure-wwdc.prompt.md** - Restructure WWDC sessions to interleave code with transcript

Use prompts with `$(cat prompts/[prompt-file])` in bash commands.

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
# Convert DOCC archive to markdown
curl -s "[json-url]" | llm -m gemini-2.5-flash -s "$(cat prompts/docc-archive.prompt.md)" > output.md
```

### Processing Other Content

For HTML pages (blogs, articles):
```bash
# Convert HTML to markdown
curl -s "[html-url]" | llm -m gemini-2.5-flash -s "$(cat prompts/html-to-markdown.prompt.md)" > output.md
```

For complex analysis across multiple files:
```bash
# Use gemini -p for analysis
gemini -p "@sources/ What are the key concurrency patterns in Swift 6.2?"
```

### WWDC Session Processing

For WWDC sessions, use the `llm` tool to convert the HTML pages directly:

```bash
# Convert WWDC session to markdown
curl -s "[wwdc-session-url]" | \
llm -m gemini-2.5-flash -s "$(cat prompts/wwdc-session.prompt.md)" > sources/wwdc/wwdc[year]-[session]-[title].md

# If needed, restructure to interleave code with transcript
llm -m gemini-2.5-flash -s "$(cat prompts/restructure-wwdc.prompt.md)" < sources/wwdc/[session-file].md > sources/wwdc/[session-file]-temp.md
mv sources/wwdc/[session-file]-temp.md sources/wwdc/[session-file].md
```

Sessions processed:
- ✅ https://developer.apple.com/videos/play/wwdc2025/266/
- ✅ https://developer.apple.com/videos/play/wwdc2025/268/
- ✅ https://developer.apple.com/videos/play/wwdc2025/270/
- ✅ https://developer.apple.com/videos/play/wwdc2023/10170/

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
curl -s "[json-url]" | llm -m gemini-2.5-flash -s "Convert this DocC archive to markdown" > output.md

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