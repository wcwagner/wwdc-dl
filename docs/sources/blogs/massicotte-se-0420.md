# SE-0420: Inheritance of actor isolation
May 9, 2024

Swift’s concurrency system seems incredibly simple *at first*. But, eventually, we all discover that there’s actually a tremendous amount of learning required to use concurrency successfully. And, one of the most challenging things is there’s also quite a bit to unlearn too. Swift concurrency has many features that *feel* familiar, but actually *work* very differently.

This [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0420-inheritance-of-actor-isolation.md) is going to help.

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](concurrency-swift-6-se-401)
*   [SE-0411: Isolated default value expressions](concurrency-swift-6-se-411)
*   [SE-0414: Region based Isolation](concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](concurrency-swift-6-se-0417)
*   [SE-0418: Inferring Sendable for methods and key path literals](concurrency-swift-6-se-0418)
*   SE-0420: Inheritance of actor isolation
*   [SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol](concurrency-swift-6-se-0421)
*   [SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts](concurrency-swift-6-se-0423)
*   [SE-0424: Custom isolation checking for SerialExecutor](concurrency-swift-6-se-0424)
*   [SE-0430:`sending` parameter and result values](concurrency-swift-6-se-0430)
*   [SE-0431: `@isolated(any)` Function Types](concurrency-swift-6-se-0431)
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# The Backstory

There was a proposal, [SE-0338](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0338-clarify-execution-non-actor-async.md), that became a little infamous. It included a major change to how async function calls work. Before this, a non-isolated async function would not change isolation. Any existing isolation would just stick.

Consider this code:

```swift
func nonIsolatedFunction() async {
}

@MainActor
func updateUI() async {
	await nonIsolatedFunction()
}
```

Prior to Swift 5.7, despite `nonIsolatedFunction` being async and requiring the `await` keyword to call, there would be **no change to isolation**. This allowed the caller of an non-isolated async function to control isolation is a very dynamic way. In the case above, `nonIsolatedFunction` would actually be on the `MainActor` when called from `updateUI`.

It was changed with SE-0338, and for good reason. It did have performance implications. But, the real issue was the dynamic behavior it allowed was unintended. The compiler just cannot reason about isolation in such situations. And, all the safety Swift concurrency brings depends on that reasoning.

**However!**

SE-0338 was *also* infamous for good reason. We are used to callers being in control. That’s how it works with threads, Dispatch, and pretty much every other concurrency system that exists aside from Swift. There was Swift code out there that felt right, worked right, but was now suddenly very wrong because it relied on this dynamic isolation inheritance that was never really supposed to be happening in the first place. Addressing these problems was not always trivial. It typically involves [isolated parameters](/isolated-parameters) or even resorting to [unsafe attributes](https://github.com/apple/swift/blob/main/docs/ReferenceGuides/UnderscoredAttributes.md#_unsafeinheritexecutor).

# The Problem

With all that set up, we can now finally get to the actual problems this proposal addresses. There are two, and the first is tiny. Isolated parameters weren’t able to capture the concept of non-isolation. You must pass in an actor here, but there isn’t an `actor` instance that represents “non-isolated”.

```swift
func doStuff(isolatedTo actor: isolated any Actor) async {
}

// how do I make this non-isolated?
await doStuff(isolatedTo: ???)
```

The second problem is the language had no convenient way to capture the current isolation. You can do this manually, but it involves boilerplate that every call site would have to deal with.

```swift
@MainActor
class MyClass {
	func doLotsOfStuff() async {
		await doStuff(isolatedTo: MainActor.shared)
		await doStuff(isolatedTo: MainActor.shared)
		await doStuff(isolatedTo: MainActor.shared)
	}
}
```

# The Solution

Fixing the inability to express “non-isolated” was easy. Isolated parameters can now accept optional arguments.

```swift
func doStuff(isolatedTo actor: isolated (any Actor)?) async {
}

// this is non-isolated
await doStuff(isolatedTo: nil)
```

And for capturing the current isolation, default arguments can now use `#isolation`, a new “special expression form”. This will capture the static isolation of the call site. It’s a lot like `#line` or `#file`, and the usage pattern is very similar. This `#isolation` expression has the type `(any Actor)?`. And that is necessary, because it is always possible for a call site to be non-isolated.

```swift
func doStuff(isolatedTo actor: isolated (any Actor)? = #isolation) async {
}

@MainActor
class MyClass {
	func doLotsOfStuff() {
		await doStuff()
		await doStuff()
		await doStuff()
	}
}
```

That definition is quite something. But, the transition from caller to callee is guaranteed to not suspend, and that is entirely controllable by the `doStuff` definition. And with this generalization, they can be used in all contexts with zero boilerplate.

You might think, as I did, that you can only use `#isolation` as a default argument for isolated parameters. But that’s not the case! It can be used for regular parameters too. I haven’t yet thought up a great use-case for doing that, but it’s worthwhile at least knowing about.

# The Implications

There are three proposals that will, in my opinion, have a profound effect on how Swift concurrency is used. The two changes here seem small. But, they take an already powerful feature and make it much nicer and more general.

Something not everyone realizes is isolated parameters prevent suspension at the call site. In fact, I was so surprised when I first learned about this I have to quote the proposal:

> Avoiding extra suspensions from actor-isolated code can also be semantically important because code from other tasks can interleave on the actor during suspensions, potentially changing the values stored in isolated storage; **this is guaranteed not to happen at the moments of call and return between functions with the same isolation**.

This is what makes isolated parameters so powerful. They make it possible to do work synchronously on function call. Now you can do that without having to clutter up the call site.

I do have some complaints, though. Sometimes, like in the case of `withCheckedContinuation`, the caller **must** be aware of this no-suspension guarantee for it to be useful. This proposal makes the lack of suspension here just as non-obvious. I kind of want there to be some kind of special keyword to make this crystal clear.

```swift
// imaginary syntax
await? withCheckedContinuation { continuation in
	// perform some work that must be done synchronously
}
```

Anyways, I’ll definitely take it.

Update: I have discovered that `with(Checked)Continuation` has been reimplemented to use this instead of `@_unsafeInheritExecutor` in the standard library!

# Will it Affect Me?

Directly? It’s possible. If you have run into cases where SE-0338 caused you problems, this could help. I certainly have hit [situations](https://github.com/ChimeHQ/AsyncXPCConnection) where I was unable to achieve correct functionality without resorting to `@_unsafeInheritExecutor`. I think I could have succeeded with just an isolated parameter in that case. But, with this proposal, I’m now certain I can.

I’ve said before that, despite being powerful, isolated parameters just aren’t a thing you need very often. I have found uses, and I know others have too. I just don’t think it’s going to come up too often in day-to-day app development. But, if you happen to have a need for them, this makes them a lot better.

Overall, this one is going to be more infrastructural. But, it *will* play a central role in the very next change, which is another big one.

---

Sponsorship helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
