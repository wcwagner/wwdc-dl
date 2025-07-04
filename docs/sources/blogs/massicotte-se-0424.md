# SE-0424: Custom isolation checking for SerialExecutor
Jun 16, 2024

This isn’t the first time in this series that custom actor executors has come up. If you recall, we got custom actor executors with [SE-0392](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0392-custom-actor-executors.md). And, just to re-iterate what I said the first time, you do not need to understand what they are to get the idea here.

What do you need to know is that custom actor executors had a limitation related to dynamic isolation. This [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0424-custom-isolation-checking-for-serialexecutor.md) fixes that.

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](concurrency-swift-6-se-401)
*   [SE-0411: Isolated default value expressions](concurrency-swift-6-se-411)
*   [SE-0414: Region based Isolation](concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](concurrency-swift-6-se-0417)
*   [SE-0418: Inferring Sendable for methods and key path literals](concurrency-swift-6-se-0418)
*   [SE-0420: Inheritance of actor isolation](concurrency-swift-6-se-0420)
*   [SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol](concurrency-swift-6-se-0421)
*   [SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts](concurrency-swift-6-se-0423)
*   SE-0424: Custom isolation checking for SerialExecutor
*   [SE-0430:`sending` parameter and result values](concurrency-swift-6-se-0430)
*   [SE-0431: `@isolated(any)` Function Types](concurrency-swift-6-se-0431)
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# The Problem

Custom actor executors help to bridge systems into Swift concurrency that don’t match its default execution model. And, dynamic isolation is all about exposing runtime isolation state to the compiler. They *mostly* work together, but there are problems.

Here’s an example of where things are logically correct, but fail at runtime:

```swift
import Dispatch

actor Caplin {
	let queue = DispatchQueue(label: "CoolQueue")

	var num = 0 // actor isolated state

	// use the queue as this actor's `SerialExecutor`
	nonisolated var unownedExecutor: UnownedSerialExecutor {
		queue.asUnownedSerialExecutor()
	}

	nonisolated func connect() {
		queue.async {
			// guaranteed to execute on `queue`
			// which is the same as self's serial executor
			self.queue.assertIsolated() // CRASH: Incorrect actor executor assumption
			self.assumeIsolated { actor in  // CRASH: Incorrect actor executor assumption
				actor.num += 1
			}
		}
	}
}
```

Look at what is going on inside of the `connect` method. This actor is using a queue as its executor. But, despite clearly being on the queue, both dynamic isolation checks will fail.

(Also, did *you* know you could just use a queue to back an actor?? And can you believe how easy it is?)

# The Solution

The proposal extends the `SerialExecutor` protocol like this:

```swift
protocol SerialExecutor: Executor {
	func checkIsolation()
}
```

Custom executors can use this facility to implement whatever logic they need to validate isolation. Here’s what the implementation looks like for `DispatchSerialQueue`:

```swift
extension DispatchQueue { 
	public func checkIsolated() {
		// make use of an existing Dispatch API to perform the validation
		dispatchPrecondition(condition: .onQueue(self))
	}
}
```

# The Implications

I think this will help to make for an even tighter integration between Swift concurrency and whatever custom execution system you’re using.

# Will it Affect Me?

If you are *implementing* a custom executor, maybe. This could help to improve the integration, internally. But, I don’t think it will have visible effects for systems that are *using* the custom executor. I think this is really cool, but ultimately, I think this is a niche within a niche. Most developers will never encounter this.

---
[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
