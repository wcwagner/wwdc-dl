---
title: 'Swift 6.2: A first look at how it''s changing Concurrency'
source: https://www.avanderlee.com/concurrency/swift-6-2-concurrency-changes/
date_crawled: '2025-07-03'
type: article
topics:
- actors
- async-await
- concurrency
- data-race-safety
- migration
- sendable
- swift6
- tasks
---

```markdown
# Swift 6.2: A first look at how it's changing Concurrency

Swift 6.2 is the upcoming release of Apple's native language. It's [currently in active development](https://github.com/swiftlang/swift/tree/release/6.2), and as you know from [my weekly Swift Evolution updates](https://www.avanderlee.com/swiftlee-weekly-subscribe/), many proposals are currently being processed. While many of you usually await a new Xcode release before jumping into new changes, I think knowing what's coming up is essential this time.

Swift 6 has been released for some time now, but many struggle to migrate their existing projects. A new project kind of works okay, but even there, it's challenging. Developers who are new to Swift get exposed to concurrency too early, leading to complex challenges to solve early in the process. The Swift team recognized this pattern and published a vision document in February 2025.

## Improving the approachability of data-race safety

The Swift team recognizes that Swift Concurrency has not been as approachable as hoped. In [their official vision document](https://github.com/swiftlang/swift-evolution/blob/main/visions/approachable-concurrency.md) they mention:

> The Swift 6 language mode provides a baseline of correctness that meets the first goal, but sometimes it comes at the cost of the second, and it can be frustrating to adopt. Now that we have a lot more user experience under our belt as a community, it’s reasonable to ask what we can do in the language to address that problem. This document lays out several potential paths for improving the usability of Swift 6, focusing on two primary use cases:
>
> 1.  Simple situations where programmers aren’t intending to use concurrency at all.
> 2.  Adapting an existing code base that uses concurrency libraries which predate Swift’s native concurrency model.

It's clear that things need to change and that's what they're actively working on. I wouldn't be surprised if they present this vision at WWDC 2025 as well, since it touches so many of us working with Swift on a daily basis.

With this document, they set the direction for the future of Swift 6. They also mention three phases on the progressive disclosure path for concurrency:

*   **Phase 1: Write simple, single-threaded code.** By default, your code runs sequentially—no parallelism, no data races, just straightforward execution.
*   **Phase 2: Write async code without data-race safety errors.** Using async/await lets you suspend execution without introducing parallelism—no shared state issues, just clean async workflows.
*   **Phase 3: Boost performance with parallelism.** Offload work from the main actor, use structured concurrency, and let Swift’s compiler keep your code safe from data races.

Or, in other words:

*   Phase 1: No concurrency at all
*   Phase 2: Suspend execution without parallism
*   Phase 3: Advanced concurrency

They are focusing on improving the language so that it becomes easier to adopt Swift Concurrency slowly. Changes are expected to reduce the number of compiler warnings and errors, and they even plan on automatic migration using a so-called migration build to accommodate these changes more easily. Some of these changes will be released in Swift 6.2.

## A closer look at the Swift 6.2 branch

When we zoom into the currently active Swift 6.2 branch, we can already see a few proposals being implemented. We can [filter on implemented proposals](https://www.swift.org/swift-evolution/#?version=6.2) at the official Swift website and find proposals related to Swift Concurrency. Here are the proposals that are either implemented or accepted at the moment of writing this article, that I believe relate to the vision document:

*   **SE-0371** [Isolated synchronous deinit](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0371-isolated-synchronous-deinit.md)
*   **SE-0461** [Run nonisolated async functions on the caller’s actor by default](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md)
*   **SE-0463** [Import Objective-C completion handler parameters as `@Sendable`](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0463-sendable-completion-handlers.md)
*   **SE-0466** [Control default actor isolation inference](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md)
*   **SE-0470** [Global-actor isolated conformance](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0470-isolated-conformances.md)

Note that these don't all mention the vision document, but they do impact Swift Concurrency's approachability.

Let me be clear that until Swift 6.2 is officially released, it's uncertain how these proposals will actually be implemented. SE-0371, for example, was planned for Swift 6.1 but was moved last minute. This shows that it's uncertain to rely on the proposals' state completely. However, we can safely assume accepted proposals will eventually make it into a future Swift release.

For now, I'd like to have a look at a few of these proposals.

### Main actor all the things!

That's a bold statement, and I'm aware, but it does explain what [SE-466](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md) will do in Swift 6.2. To quote the proposal's introduction:

> This proposal introduces a new compiler setting for inferring `@MainActor` isolation by default within the module to mitigate false-positive data-race safety errors in sequential code.

Most code we write is single-threaded. Apps, scripts, and command-line tools usually run on the main actor by default, and unless you explicitly introduce concurrency—like by creating a Task—everything just runs sequentially.

In these cases, data races aren’t even possible, so any concurrency warning is essentially a false alarm. This proposal aims to recognize that, so we don't get overwhelmed with unnecessary warnings. Especially for beginners, it’s important to keep things simple—many start out with these straightforward programs, and if we don’t force them to learn concurrency concepts too early, the language becomes a lot more welcoming.

This change is source incompatible and will be opt-in for existing projects via `-default-isolation MainActor` or `defaultIsolation(MainActor.self)` in a package manifest. Obviously, this will become much clearer when Swift 6.2 gets officially released.

### Running nonisolated async functions on the caller’s actor by default

You've probably learned the differences between nonisolated and isolated in my dedicated article. Interestingly enough, the compiler currently evaluates nonisolated synchronous and asynchronous methods differently. This is confusing, and that's what [SE-461](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md) will change.

The proposal contains many details and quite a few new attributes, too. I won't dive into details too much since this proposal is still in development, and some of these attributes might only be used for advanced use cases. However, there's one crucial thing that I would like to highlight.

Take the following code example that demonstrates on which thread an asynchronous task executes:

```swift
class NotSendable {
    func performAsync() async {
        print("Task started on thread: \(Thread.currentThread)")
        // Current (old) situation: Task started on thread: <NSThread: 0x600003694d00>{number = 8, name = (null)}
    }
}

@MainActor
struct NewThreadingDemonstrator {
    
    func demonstrate() async {
        print("Starting on the main thread: \(Thread.currentThread)")
        // Prints: Starting on the main thread: <_NSMainThread: 0x6000006b4040>{number = 1, name = main}

        let notSendable = NotSendable()
        await notSendable.performAsync()
        
        /// Returning on the main thread.
        print("Resuming on the main thread: \(Thread.currentThread)")
        // Prints: Resuming on the main thread: <_NSMainThread: 0x6000006b4040>{number = 1, name = main}
    }
}
```

As you can see, the async task does not inherit the caller's actor isolation. If it were, we would see the main thread being printed inside `performAsync`. This demonstrates how we potentially get exposed to Swift Concurrency early in the process of working with Swift—you simply call into an asynchronous method, which results in a multi-threaded application that risks potential data races.

This behavior is especially important for preventing unexpected overhang on the main actor. In the end, we often want asynchronous methods to be dispatched to a different thread so our programs can continue execution while awaiting the results.

For those wondering, I'm using the following extension to allow printing out the current thread:

```swift
extension Thread {
    /// A convenience method to print out the current thread from an async method.
    /// This is a workaround for compiler error:
    /// Class property 'current' is unavailable from asynchronous contexts; Thread.current cannot be used from async contexts.
    /// See: https://github.com/swiftlang/swift-corelibs-foundation/issues/5139
    public static var currentThread: Thread {
        return Thread.current
    }
}
```

I've downloaded the latest `main` branch development toolchain and compiled the same code using the `AsyncCallerExecution` upcoming feature flag. This is the result after enabling:

```swift
class NotSendable {
    func performAsync() async {
        print("Task started on thread: \(Thread.currentThread)")
        // Old situation: Task started on thread: <NSThread: 0x600003694d00>{number = 8, name = (null)}
        // New situation: Task started on thread: <_NSMainThread: 0x6000006b4040>{number = 1, name = main}
    }
}

@MainActor
struct NewThreadingDemonstrator {
    
    func demonstrate() async {
        print("Starting on the main thread: \(Thread.currentThread)")
        // Prints: Starting on the main thread: <_NSMainThread: 0x6000006b4040>{number = 1, name = main}

        let notSendable = NotSendable()
        await notSendable.performAsync()
        
        /// Returning on the main thread.
        print("Resuming on the main thread: \(Thread.currentThread)")
        // Prints: Resuming on the main thread: <_NSMainThread: 0x6000006b4040>{number = 1, name = main}
    }
}
```

As you can see, `someAsyncTask` now inherits the actor isolation from its caller. There will be ways to opt out of inheritance described in the proposal, but these are not yet available in the latest toolchain. This will definitely become clearer as soon as Swift 6.2 gets released.

## Conclusion

Swift Concurrency is getting improved in Swift 6.2 to make it more approachable. This will impact existing projects positively too, but it will require some additional changes like several opt-ins. Eventually, it should be easier to adopt Swift 6 and newcomers to the language will likely get exposed to Swift Concurrency at a later stage.

It’s an exciting time as a Swift developer, and it’s never been a better time to start investing in your concurrency knowledge. Start writing efficient, thread-safe code and adopt Swift Concurrency using my dedicated course:

→ [Go to swiftconcurrencycourse.com](https://www.swiftconcurrencycourse.com?utm_source=swiftlee&utm_medium=article&utm_campaign=course_launch)

I hope to see you there!
```
