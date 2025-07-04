# SE-0430: `sending` parameter and result values

Jun 21, 2024

Everyone seems excited about [region-based isolation](concurrency-swift-6-se-0414). And they should be! It is a pretty amazing technology that will reduce the need for `Sendable` types. However, it does has limitations. It’s still fairly easy to come up with safe patterns the compiler cannot understand.

This [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0430-transferring-parameters-and-results.md) introduces some new syntax that can really help.

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
*   SE-0430: `sending` parameter and result values
*   [SE-0431: `@isolated(any)` Function Types](concurrency-swift-6-se-0431)
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# The Problem

Region-based isolation is a static code analysis tool. To do the analysis, tools like this need to see all possible code paths. This means they work really well at understanding function **bodies**, but have a hard time with function **calls**. There may be no source code available for a function, so how could it possibly understand what a call does?

Here’s a trivial example:

```swift
class NonSendable {
}

@MainActor func someMainFunction(_ ns: NonSendable) {
}

func trySend(ns: NonSendable) async {
	// error: sending 'ns' can result in data races.
	await someMainFunction(ns)
}
```

This feels silly. But it totally *does* make sense, because the compiler cannot know how the `ns` variable is being used at all possible call sites of `trySend`. In fact, it’s completely possible that some are safe while others are not. This is a shame, because we can clearly see that this pattern could at least *potentially* be safe.

# The Solution

Lots of code analysis tools have to face these kinds of problems. It is typically tackled by adding metadata somehow so the tools can “see” how the functions can be used. The proposal goes that route too, by introducing the new contextual keyword `sending`.

```swift
func trySend(ns: sending NonSendable) async {
	// this is now ok
	await someMainFunction(ns)
}
```

When you mark parameters `sending`, you are adding a constraint. At all call sites, you are *requiring* that the compiler be able to prove the argument can safely cross an isolation domain. This constraint on the outside of the function has the effect of *relaxing* constraints on the inside. The compiler can now reason about the safety of the parameter because it has more information.

This works in reverse for `sending` return values.

```swift
func getNonSendable() -> sending NonSendable {
	// ...
}
```

When a return value is marked `sending` it is *adding* constraints to the function implementation, but removing them from callers. Values that get returned from such of a function can better participate in region-based isolation without clients having to do anything.

# The Implications

Before this proposal, there were many patterns that required the use of `Sendable` types. And that can be really hard to pull off. The `sending` keyword is a great way to relax these requirements. In fact, many of Swift’s own concurrency APIs are adopting `sending`. Of particular note is the closure argument to `Task.init`. This means its captures no longer need to be `Sendable`, as long as they can still be proven safe at the point of capture. This is quite something.

# Will it Affect Me?

You don’t have to use, or even understand this keyword to benefit from it. It is giving the language a tool to relax sendability requirements even further. The standard library is adopting it right away. But, if you make an API, especially if it uses `@Sendable` closures, this is absolutely worth looking at. `Sendable` is a very high bar, and `sending` makes it less necessary.

Region-based isolation is really cool, and this makes it much more powerful.

---

Sponsorship helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
