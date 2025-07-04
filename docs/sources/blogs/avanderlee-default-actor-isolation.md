---
title: Default Actor Isolation in Swift 6.2
source: https://www.avanderlee.com/concurrency/default-actor-isolation-in-swift-6-2/
date_crawled: '2025-07-03'
type: article
topics:
- actors
- async-await
- concurrency
- data-race-safety
- migration
- swift6
- tasks
---

```markdown
# Default Actor Isolation in Swift 6.2

Default Actor Isolation in Swift 6.2 allows you to run code on the `@MainActor` by default. This new Swift compiler setting helps improve the approachability of data-race safety, which was set as a goal for the Swift team in [their February 2025 vision document](https://github.com/swiftlang/swift-evolution/blob/main/visions/approachable-concurrency.md#risks-of-a-language-dialect).

While new projects are set to `@MainActor` isolation by default, existing projects will continue to use the old non-isolated setting. This impacts the number of warnings and compiler errors you'll get when migrating quite a bit, so it's essential to understand this new compiler setting when migrating your project to Swift 6 and above.

## What is Default Actor Isolation?

Default Actor Isolation is a new Swift compiler setting that alters the default behavior of concurrency isolation. Instead of assuming no isolation, like Swift did before, it now assumes that your code should run on the `@MainActor` unless you say otherwise.

When you don’t explicitly mark a function or property with `nonisolated` or another actor, Swift treats it as isolated to the `MainActor`. This behavior is especially useful in app development because most UI-related code is expected to run on the main thread.

## How to set the Default Actor Isolation to @MainActor

While new projects will already use the main actor as their default isolation, existing projects need to opt in explicitly. You can do so by changing the Swift Compiler setting in your Xcode Project:

![Default Actor Isolation in Xcode Build Settings](https://www.avanderlee.com/wp-content/smush-webp/2025/06/default_actor_isolation_main_actor-1024x578.png.webp)

Enabling this setting causes declarations to default to `@MainActor` isolation unless explicitly marked as `nonisolated` or assigned to a different actor.

### Changing the Default Actor Isolation for Swift packages

Changing the Default Actor Isolation in your Xcode project only affects that project. You'll also need to update it for each package. You can do so by adding the following Swift setting:

```swift
.target(
    name: "DefaultActorIsolationPackage",
    swiftSettings: [
        /// You can add a new `defaultIsolation` Swift setting to any of your SPM targets.
        .defaultIsolation(MainActor.self)
    ]
)
```

Make sure to set your package Swift version to 6.2 to ensure this setting becomes available:

```swift
// swift-tools-version: 6.2
// The swift-tools-version declares the minimum version of Swift required to build this package.
```

## How running on the @MainActor by default helps migration

Migrating to Swift 6 introduces a lot of stricter rules around concurrency. Without default actor isolation, the compiler assumes that your code is nonisolated, allowing access from any thread. This often leads to a flood of warnings and errors when working with code that interacts with the UI or performs other main-thread-only work. I'm sure many of you have been adding `@MainActor` in many places, only to find out more warnings and errors will show up after compilation.

By enabling `@MainActor` as the default, Swift helps reduce that noise. A lot of your existing code, especially UI code, already assumes it’s running on the main thread. With default isolation in place, the compiler aligns with that assumption, so you don’t have to mark every method or property with ` @MainActor ` explicitly.

Migrating a UI-heavy app? Enabling this setting makes the transition to Swift 6’s stricter concurrency model much smoother.

## So, should I wait for migrating until Xcode 26?

In my opinion, yes! Even more so since the Swift team is currently working on migration solutions. These migrations will impact changing to `@concurrent` (see my other article), as well as other Swift 6.2 related changes. I suggest continuing migration with the latest Xcode 26 beta or downloading the newest Swift toolchain to access migration solutions as they become available. By the time the release candidate of Xcode 26 arrives, you'll be in good shape to complete your migration.

### A dedicated course to help you with Swift Concurrency

This article provides a short introduction to one of the many Swift Concurrency changes announced at WWDC 2025. My course will guide you further and allows you to learn everything regarding async/await, actors, tasks, and migrating to Swift 6.2.

You can check out [swiftconcurrencycourse.com](http://swiftconcurrencycourse.com) to learn more.

**Conclusion**

Default Actor Isolation is a big step forward in making Swift Concurrency more approachable. Many apps start as single-threaded, so it makes a lot of sense to introduce concurrency at a later step. It's also a great way to reduce noise, preventing you from having to add `@MainActor` in many places manually.

If you’re ready to learn more about Swift Concurrency, I invite you to check out my dedicated course for a seamless Swift 6 migration: [swiftconcurrencycourse.com](https://www.swiftconcurrencycourse.com).

Thanks!
```
