# Crawled URLs Tracker

This file tracks all URLs crawled for the Swift 6.2 Concurrency Documentation project.

## Format
Each entry includes:
- **URL**: The source URL
- **Date**: When it was crawled
- **Output**: Where the markdown file is saved
- **Type**: Content type (article, symbol, collection, code sample, etc.)
- **Notes**: Brief description of content

---

## Swift.org Documentation

| URL | Date | Output | Type | Notes |
|-----|------|--------|------|-------|
| https://www.swift.org/migration/documentation/migrationguide/ | 2025-07-04 | sources/swift-org/swift-6-migration-guide.md | article | Main migration guide overview |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/dataracesafety/ | 2025-07-04 | sources/swift-org/data-race-safety.md | article | Fundamental concepts for data-race-free code |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/migrationstrategy/ | 2025-07-04 | sources/swift-org/migration-strategy.md | article | Strategies for migrating to Swift 6 |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/completechecking/ | 2025-07-04 | sources/swift-org/complete-checking.md | article | Enabling complete concurrency checking |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/swift6mode/ | 2025-07-04 | sources/swift-org/swift-6-mode.md | article | Enabling Swift 6 language mode |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/commonproblems/ | 2025-07-04 | sources/swift-org/common-problems.md | article | Common migration problems and solutions |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/incrementaladoption/ | 2025-07-04 | sources/swift-org/incremental-adoption.md | article | Incremental adoption strategies |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/sourcecompatibility/ | 2025-07-04 | sources/swift-org/source-compatibility.md | article | Source compatibility considerations |
| https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/libraryevolution/ | 2025-07-04 | sources/swift-org/library-evolution.md | article | Library evolution and concurrency |
| https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/ | 2025-07-04 | sources/swift-org/swift-book-concurrency.md | tutorial | Swift Book chapter on concurrency |

## Apple Developer Documentation (DOCC)

| URL | Date | Output | Type | Notes |
|-----|------|--------|------|-------|
| https://developer.apple.com/documentation/swift/updating_an_app_to_use_swift_concurrency | 2025-07-04 | sources/apple-dev/updating-app-swift-concurrency.md | article | Guide for updating apps to use Swift concurrency |

## Community Blogs

| URL | Date | Output | Type | Notes |
|-----|------|--------|------|-------|
| https://www.hackingwithswift.com/articles/277/whats-new-in-swift-6-2 | 2025-07-04 | sources/blogs/hackingwithswift-swift-6-2.md | article | What's new in Swift 6.2 - comprehensive overview |
| https://www.avanderlee.com/concurrency/swift-6-2-concurrency-changes/ | 2025-07-04 | sources/blogs/avanderlee-swift-6-2-concurrency.md | article | Swift 6.2 concurrency changes |
| https://www.avanderlee.com/concurrency/default-actor-isolation-in-swift-6-2/ | 2025-07-04 | sources/blogs/avanderlee-default-actor-isolation.md | article | Default actor isolation in Swift 6.2 |
| https://www.avanderlee.com/concurrency/swift-6-migrating-xcode-projects-packages/ | 2025-07-04 | sources/blogs/avanderlee-swift-6-migration.md | article | Migrating to Swift 6 - Xcode projects and packages |

## GitHub Repositories

| URL | Date | Output | Type | Notes |
|-----|------|--------|------|-------|
| https://github.com/LucasVanDongen/Modern-Concurrency-2025 | 2025-07-04 | sources/github/modern-concurrency-2025-readme.md | repository | Modern Concurrency patterns and examples |
| https://github.com/LucasVanDongen/Modern-Concurrency-2025 | 2025-07-04 | sources/github/modern-concurrency-2025-examples.md | summary | Key examples overview |

## WWDC Sessions

| Session | Date | Output | Type | Notes |
|---------|------|--------|------|-------|
| https://developer.apple.com/videos/play/wwdc2025/266/ | 2025-07-04 | sources/wwdc/wwdc2025-266-explore-concurrency-in-swiftui.md | video | Explore concurrency in SwiftUI |
| https://developer.apple.com/videos/play/wwdc2025/268/ | 2025-07-04 | sources/wwdc/wwdc2025-268-embracing-swift-concurrency.md | video | Embracing Swift concurrency |
| https://developer.apple.com/videos/play/wwdc2025/270/ | 2025-07-04 | sources/wwdc/wwdc2025-270-code-along-elevate-app-swift-concurrency.md | video | Code-along: Elevate an app with Swift concurrency |
| https://developer.apple.com/videos/play/wwdc2023/10170/ | 2025-07-04 | sources/wwdc/wwdc2023-10170-beyond-basics-structured-concurrency.md | video | Beyond the basics of structured concurrency |

---

## Seed URLs (To Process)

### Swift.org
- https://www.swift.org/migration/documentation/migrationguide/
- https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/

### Apple Developer (Need JSON conversion)
- https://developer.apple.com/documentation/swift/updating_an_app_to_use_swift_concurrency

### Community
- https://www.avanderlee.com/category/concurrency/
- https://www.donnywals.com/the-blog/
- https://www.hackingwithswift.com/articles/277/whats-new-in-swift-6-2
- https://github.com/LucasVanDongen/Modern-Concurrency-2025

### WWDC Videos
- https://developer.apple.com/videos/play/wwdc2025/266/
- https://developer.apple.com/videos/play/wwdc2025/268/
- https://developer.apple.com/videos/play/wwdc2025/270/
- https://developer.apple.com/videos/play/wwdc2023/10170/