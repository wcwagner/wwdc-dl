# SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts

Lots of people have been turning on strict concurrency and fixing up warnings. But, the reality is, Swift developers will be mixing Swift 6 and non-Swift 6 code for years to come. This [proposal](https://github.com/apple/swift-evolution/blob/main/proposals/0423-dynamic-actor-isolation.md) is all about making this simultaneously easier and safer at the same time.

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](concurrency-swift-6-se-401)
*   [SE-0411: Isolated default value expressions](concurrency-swift-6-se-411)
*   [SE-0414: Region based Isolation](concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](concurrency-swift-6-se-0417)
*   [SE-0418: Inferring Sendable for methods and key path literals](concurrency-swift-6-se-0418)
*   [SE-0420: Inheritance of actor isolation](concurrency-swift-6-se-0420)
*   [SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol](concurrency-swift-6-se-0421)
*   SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts
*   [SE-0424: Custom isolation checking for SerialExecutor](concurrency-swift-6-se-0424)
*   [SE-0430: `sending` parameter and result values](concurrency-swift-6-se-0430)
*   [SE-0431: `@isolated(any)` Function Types](concurrency-swift-6-se-0431)
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# The Problem

Have you ever used a protocol before? Apparently they are quite popular. The thing is, despite being very widely used, protocols are actually be quite tricky when it comes to concurrency. And this is especially true when the protocol in question was designed without complete checking in mind.

```swift
// Defined in some module
public protocol ViewDelegateProtocol {
	func respondToUIEvent()
}

// your code
@MainActor
class MyViewController: ViewDelegateProtocol {
	// Warning: @MainActor function cannot satisfy a nonisolated requirement
	func respondToUIEvent() { 
	}
}
```

There’s a now pretty-widely known workaround, but it’s gross. First, you make your method non-isolated to match the protocol, and then you immediately re-establish isolation dynamically.

```swift
@MainActor
class MyViewController: ViewDelegateProtocol {
	nonisolated func respondToUIEvent() {
		MainActor.assumeIsolated {
		}
	}
}
```

While this works, it has more problems than just the boilerplate. The `respondToUIEvent` method now doesn’t have correct static isolation. That means it can be called from other non-isolated contexts within the class.

# The Solution

This proposal adds the ability to annotate a conformance with `@preconcurrency`. When you do this, it has the same runtime effect as the previous workaround, but *without* sacrificing static isolation.

```swift
@MainActor
class MyViewController: @preconcurrency ViewDelegateProtocol {
	func respondToUIEvent() {
		// no need for nonisolated!
	}
}
```

# The Implications

The need for this nonisolated-assumeIsolated dance is very common, and it’s just a pain. This proposal makes it so much nicer, and also safer. It actually introduces a number of other safety checks too, that will ensure that the code you think is running on the main thread actually is.

# Will it Affect Me?

Concise, convenient, and safer way to use protocols. Helps improve interoperability with non-Swift 6 code. No new syntax. 💯

---
[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing.
I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
