Here's the Markdown conversion of the provided HTML:

# A Swift Concurrency Glossary
Jan 25, 2025

It would be nice if there was a single place to go to look up all the terms, keywords, and annotations related to Swift concurrency. So here it is. By **no means** do you need to understand everything here to use concurrency successfully. Let me know what I forgot!

Oh and of course, I included some commentary.

## `actor`

*   Type: Keyword
*   Usage: Defines a new reference type that protects mutable state
*   Introduced: [SE-0306](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0306-actors.md) Actors

Actors are the thing that define a unit of isolation. They are easy to **make**, but require a fair bit of understanding and practice to use successfully.

## [Actor](https://developer.apple.com/documentation/swift/actor)

*   Type: Protocol
*   Usage: A protocol which all actor types conform to
*   Introduced: [SE-0306](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0306-actors.md) Actors

This is kinda like `AnyObject`, but only for actor types. You’ll rarely need this, aside from making isolated parameters.

## `async`

*   Type: keyword
*   Usage: Applied to a function signature so it can be used with `await`
*   Introduced: [SE-0296](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0296-async-await.md) Async/await

This keyword marks an "[effect](https://en.wikipedia.org/wiki/Effect_system)" on a function, allowing it to use `await` internally and also be itself awaited.

## [AsyncSequence](https://developer.apple.com/documentation/swift/asyncsequence)

*   Type: Protocol
*   Usage: A series of value that are produced over time
*   Introduced: [SE-0298](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0298-asyncsequence.md) Async/Await: Sequences

This is a protocol that describes a sequence who’s values may only be available at some point in the future.

## `async let`

*   Type: Flow Control
*   Usage: Convenient shortcut to wrap work in a new Task
*   Introduced: [SE-03017](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0317-async-let.md) `async let` bindings

This one gives you a way to begin some work asynchronously without needing to await immediately. Many useful applications, but comes with some subtly.

## `await`

*   Type: keyword
*   Usage: Marks a suspension point that allows an async function to execute
*   Introduced: [SE-0296](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0296-async-await.md) Async/await

The other half of `async`. You use this to introduce a potential suspension point in the currently executing task. At these points, the actor executing code can change.

## Continuations

*   Type: Type
*   Usage: Makes it possible to wrap up callback-based code so it can be used with `await`
*   Introduced: [SE-0300](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0300-continuation.md) Continuations for interfacing async tasks with synchronous code

Asynchronous execution is not new. But, it was very commonly done using callbacks and closures. This is a whole suite of APIs that allows you to express these concepts in terms of async functions.

## [Executor](https://developer.apple.com/documentation/swift/executor)

*   Type: Protocol
*   Usage: An API for expressing how actors execute code
*   Introduced: [SE-0304](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0304-structured-concurrency.md) Structured concurrency

There is a pretty large set of APIs for controlling and interacting with the underlying mechanisms an actor uses to run code. This is rarely required for day-to-day Swift development, but is there for advanced uses and performance considerations.

## `for-await`

*   Type: Flow Control
*   Usage: Get the values from an `AsyncSequence`
*   Introduced: [SE-0298](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0298-asyncsequence.md) Async/Await: Sequences

This gives you a way to retrieve the values in an `AsyncSequence` via a control structure that very closely resembles a traditional for loop.

## `@globalActor`

*   Type: annotation
*   Usage: Marks an actor type as global, allowing it to be used as a global actor annotation
*   Introduced: [SE-0316](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0316-global-actors.md) Global actors

This is how you make an actor type “global”. A global actor’s type name can be referenced in annotation form, and can be used to apply static isolation.

## Global Executor

*   Type: concept
*   Usage: The executor that runs non-isolated code
*   Introduced: [SE-0338](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0338-clarify-execution-non-actor-async.md) Clarify the Execution of Non-Actor-Isolated Async Functions

If actors run code they isolate on their executor, where does non-isolated code run? It runs on the “Global Executor”. Unlike actor executors, this one is **not** serial, and can run more than one thing simultaneously.

## `isolated`

*   Type: keyword
*   Usage: Defines static isolation via a parameter of a function
*   Introduced: [SE-0313](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0313-actor-isolation-control.md) Improved control over actor isolation

There are four ways to define isolation statically, with this being the most powerful and complex. This is an essential tool **if** you need to integrate concurrency into non-`Sendable` types.

(There’s [work](https://forums.swift.org/t/pitch-inherit-isolation-by-default-for-async-functions/74862) going on to simplify this area! I’ve also written something about how to [use it](/non-sendable) with non-Sendable types.)

## `@isolated(any)`

*   Type: annotation
*   Usage: Makes it possible to inspect a function’s static isolation at runtime
*   Introduced: [SE-0431](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0431-isolated-any-functions.md) `@isolated(any)` Function Types

There are rare cases where you may want to inspect the static isolation was of a function that has been passed around as a variable. This annotations makes that possible. If you are thinking about this, you probably want to combine it with `@_inheritActorContext`.

(I’ve written about [this one](/concurrency-swift-6-se-0431) specifically.)

## isolation

*   Type: concept
*   Usage: The form of thread-safety that an actor type provides
*   Introduced: [SE-0306](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0306-actors.md) Actors

Isolation is this abstraction over ways to make things thread-safe. Actors are the things that implement that safety, perhaps via a serial queue.

(I’ve got two things on this. One about how you [use isolation](/intro-to-isolation) and another to help [think](/isolation-intuition) about it.)

## [#isolation](https://developer.apple.com/documentation/swift/isolation())

*   Type: expression macro
*   Usage: Returns the static isolation as `(any Actor)?`
*   Introduced: [SE-0420](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0420-inheritance-of-actor-isolation.md) Inheritance of actor isolation

If you are using an isolated parameter, you **may** want to use this as well. I also have found it handy for printing out what the compiler thinks the isolation is at a specific point.

(I’ve written about [this one](/concurrency-swift-6-se-0420) as well.)

## `@_inheritActorContext`

*   Type: parameter annotation
*   Usage: Applies isolation inheritance to a closure parameter
*   Introduced: ?

You can use this one to match the sematics of `Task`, so a closure can maintain the same isolation as where it was formed. Usually goes together with `@isolated(any)`.

(There is a [proposal](https://forums.swift.org/t/closure-isolation-control/70378) floating around that will formalize this one, though I do have [complex feelings](https://forums.swift.org/t/distinction-between-isolated-any-and-inheritactorcontext/75730) about it.)

## `@MainActor`

*   Type: annotation
*   Usage: The global actor annotation for the `MainActor` type
*   Introduced: [SE-0316](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0316-global-actors.md) Global actors

I bet you’ve come across this one before. It is just how you reference the shared `MainActor` instance.

## `nonisolated`

*   Type: keyword
*   Usage: Explicitly turn off actor isolation for a declaration
*   Introduced: [SE-0313](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0313-actor-isolation-control.md) Improved control over actor isolation

Actors provide isolation, but sometimes you want to disable that. This is a handy way to hop off an actor to run some code in the background.

## `@preconcurrency`

*   Type: attribute
*   Usage: Multiple, all around how code built for Swift 6 interacts with code that has not
*   Introduced: [SE-0337](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0337-support-incremental-migration-to-concurrency-checking.md) Incremental migration to concurrency checking, [SE-0423](https://github.com/apple/swift-evolution/blob/main/proposals/0423-dynamic-actor-isolation.md): Dynamic actor isolation enforcement from non-strict-concurrency contexts

If you are consuming APIs written before Swift 6, or making APIs that need to remain compatible with Swift 5 mode, you pretty much need this one.

(I’ve gone into some depth about [how this works](/preconcurrency).)

## Region-Based Isolation

*   Type: concept
*   Usage: Allows the compiler to relax `Sendable` checking in specific circumstances
*   Introduced: [SE-0414](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0414-region-based-isolation.md) Region-based Isolation

This is a code-flow analysis system that allows the compiler to prove that even if a type is not `Sendable`, a specific usage pattern may still always be safe. It can really only work within the scope of a single function body, but the `sending` keyword does allow it to be even more powerful.

(My summary of this is [here](/concurrency-swift-6-se-0414).)

## [Sendable](https://developer.apple.com/documentation/swift/sendable)

*   Type: Protocol
*   Usage: A marker protocol that indicates a type can be safely used from any isolation, including none at all
*   Introduced: [SE-0302](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0302-concurrent-value-and-concurrent-closures.md) Sendable and `@Sendable` closures

This provides a way to encode the thread-safety of a type into the type system. And it has no members so how complex could it possibly be?

(I haven’t even written about this directly, but I did cover the general idea [here](/non-sendable).)

## `@Sendable`

*   Type: Attribute
*   Usage: Functions cannot conform to protocols, so an attribute is required to express the same concept
*   Introduced: [SE-0302](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0302-concurrent-value-and-concurrent-closures.md) Sendable and `@Sendable` closures

This is exactly the same thing as `Sendable`, but for function types.

## `sending`

*   Type: Keyword
*   Usage: Express the concurrent usage of parameters and return values into the type system
*   Introduced: [SE-0430](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0430-transferring-parameters-and-results.md) `sending` parameter and result values

Sometimes `Sendable`/`@Sendable` is too difficult or just unnecessarily restrictive. The `sending` keyword is a way relax some constraints by encoding a strict promise about the behavior of values into your function signatures.

(And, yes, I did in fact [write](/concurrency-swift-6-se-0430) about it!)

## [Task](https://developer.apple.com/documentation/swift/task)

*   Type: Type
*   Usage: Creates a new top-level context to run async code
*   Introduced: [SE-0304](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0304-structured-concurrency.md) Structured concurrency

You gotta start somewhere, and for async functions it’s usually via a `Task`. But this type somes with a lot of features, to support things like cancellation and accessing results.

## [TaskGroup](https://developer.apple.com/documentation/swift/taskgroup)

*   Type: Type
*   Usage: An API to work with an arbitrary number of child tasks
*   Introduced: [SE-0304](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0304-structured-concurrency.md) Structured concurrency

A `TaskGroup` gives you a way to manage and control multiple child `Task` instances. Useful for tackling a variety of problems, including just doing a bunch of stuff simultaneously.

## [TaskLocal](https://developer.apple.com/documentation/swift/tasklocal)

*   Type: Type
*   Usage: A mechanism for making values available across the current task
*   Introduced: [SE-0311](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0311-task-locals.md) Task Local Values

This is kind of like the analog of thread-local values, but for tasks. They are quite an advanced tool, but there are lots of clever/tricky things you can pull off with them.

## `@unchecked`

*   Type: Annotation
*   Usage: Disables compiler checks for a `Sendable` conformance
*   Introduced: [SE-0302](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0302-concurrent-value-and-concurrent-closures.md) Sendable and `@Sendable` closures

Sometimes, you’ve already got thread-safety implemented, but it is done via a mechanism don’t support Swift’s compiler-based checking. Declaring a type `@unchecked Sendable` let’s you express that situation.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
