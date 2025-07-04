# SE-0431: `@isolated(any)` Function Types

Jul 5, 2024

Swift uses its type system to model concurrency. An integral part of that system is **functions**. Swift’s ability to model how functions can behave has expanded pretty dramatically lately. Except, there’s a substantial gap. We’ve seen many new facilities for expressing concurrency in function *declarations*.

This [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0431-isolated-any-functions.md) adds a new capability to function *values*.

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](concurrency-swift-6-se-401)
*   [SE-0411: Isolated default value expressions](concurrency-swift-6-se-411)
*   [SE-0414: Region based Isolation](concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](concurrency-swift-6-se-0417)
*   [SE-0418: Inferring Sendable for methods and key path literals](concurrency-swift-6-se-0418)
*   [SE-0420: Inheritance of actor isolation](concurrency-swift-6-se-0420)
*   [SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol](concurrency-swift-6-se-0421)
*   [SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts](concurrency-swift-6-se-0423)
*   [SE-0424: Custom isolation checking for SerialExecutor](concurrency-swift-6-se-0424)
*   [SE-0430: `sending` parameter and result values](concurrency-swift-6-se-0430)
*   SE-0431: `@isolated(any)` Function Types
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# The Problem

Every declaration in Swift has some well-defined static isolation. You can **always** determine what the isolation is through code inspection. Closures, however, are special. Their isolation is influenced not just by *where* they are defined, but also by *what* they capture.

This sounds complicated. But, in practice you rarely need to understand or even think about these details. All you need to know is this:

The context of a closure definition matters, but that context is also **lost** when you pass it around.

```swift
func scheduleSomeWork(_ f: @escaping @Sendable () async -> Void) {
	// We've lost all the static isolation information
	// available where f was defined.
	Task {
		await f()
	}
}

func defineClosure() {
	scheduleSomeWork { @MainActor in
		print("I'm on the main actor")
	}
}
```

Here, we’re defining a closure which will run on the `@MainActor`. But, that isolation is only statically visible in `defineClosure`.

At this point, you may be thinking “okaay, but I don’t get why this is a problem”. And, I’m not surprised, because there aren’t too many situations where this will matter. There is, however, one really important place where it makes a big difference: the `Task` creation APIs.

These create a new top-level asynchronous task. But, which actor should that task run on? This information is encoded in the closure body. When looking at the function’s *type*, it’s completely invisible.

But `Task` has to start somewhere, so it first begins with a global executor context. And then the very next thing that happens is the closure hops over to the correct actor. This double hop, aside from being inefficient, has a very significant programmer-visible effect: `Task` does not preserve order.

```swift
Task { print("a") }
Task { print("b") }
Task { print("c") }
```

The ordering here is not well-defined. I have, personally, found this to be extremely difficult to deal with. It makes it incredibly hard to introduce async contexts incrementally. And honestly it’s just really confusing.

# The Solution

This proposal makes it possible to inspect a function value’s isolation. A closure annotated with `@isolated(any)` can expose its captured isolation *at runtime*.

```swift
func scheduleSomeWork(_ f: @escaping @Sendable @isolated(any) () async -> Void) {
	// closures have properties now!
	let isolation = f.isolation

	// do something with "isolation" I guess?
}
```

When I first saw this, my initial reaction was confusion. Closures have properties? That looks weird. And then I was like, yeah it’s just a type of course it can have properties. It’s actually kind of weird they **didn’t** have properties before. The type of the `isolation` property matches isolated parameters: `(any Actor)?`.

Aside from making this property available, this annotation has a small effect on semantics. Adding `@isolated(any)` to a closure means it **must** be called with an `await`. This is true even it does not cross an isolation boundary.

# The Implications

I think it was one of those problems that had a bunch of superficial solutions. But, to me, this looks like the exact opposite. This is a deep, fundamental extension to function types. **A lot** of thought went into this proposal. This could have easily been just `@isolated`. But, it is leaving the door open for a future revision that can capture not just the isolation value but also its **type**.

Undefined `Task` ordering has caused me **a lot** of issues. It took me a while to even realize it was happening. Thanks to this proposal, `Task` can now **synchronously** enqueue work onto executors.

However, I really do want to stress that “well-defined” ordering for `Task` creation is not the same as “FIFO”. A high priority task can still execute before more-recently-created lower-priority tasks.

# Will it Affect Me?

You definitely want to adopt this if you are passing a closure parameter directly into one of the standard library’s task creation APIs. Aside from that use-case, I still don’t have a great feel for when or why you would choose to annotate a parameter with `@isolated(any)`. I don’t think there are any *downsides* if the closure is already `async`. And, it does buy you some future flexibility. But, I wouldn’t recommend it unless you have a clear idea of why it would be necessary.

```swift
Task { print("a") }
Task { print("b") }
Task { print("c") }
```

But, while we’re all thinking on that, let’s also take a moment to celebrate that when compiled with Swift 6, this now always prints:

“a”
“b”
“c”

🎉

(Update: I always forget that this ordering applies **exclusively** to isolated contexts. Without an actor, `Task` execution order remains undefined.)

---
[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
