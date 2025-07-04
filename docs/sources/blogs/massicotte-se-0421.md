SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol
May 13, 2024

Have you ever wanted to use `some AsyncSequence`? I certainly have. The inability to hide the implementation type of an `AsyncSequence` is an enormous pain. It is particularly problematic when trying to replace Combine with [AsyncAlgorithms](https://github.com/apple/swift-async-algorithms). There are some libraries out there that help, but I’d really like this problem to just disappear.

This [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0421-generalize-async-sequence.md) **finally** addresses this! And, on top of that, it fixes a correctness issue, makes `AsyncIteratorProtocol` more efficient, and makes it easier to use non-Sendable types. Let’s go!

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](concurrency-swift-6-se-401)
*   [SE-0411: Isolated default value expressions](concurrency-swift-6-se-411)
*   [SE-0414: Region based Isolation](concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](concurrency-swift-6-se-0417)
*   [SE-0418: Inferring Sendable for methods and key path literals](concurrency-swift-6-se-0418)
*   [SE-0420: Inheritance of actor isolation](concurrency-swift-6-se-0420)
*   SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol
*   [SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts](concurrency-swift-6-se-0423)
*   [SE-0424: Custom isolation checking for SerialExecutor](concurrency-swift-6-se-0424)
*   [SE-0430:`sending` parameter and result values](concurrency-swift-6-se-0430)
*   [SE-0431: `@isolated(any)` Function Types](concurrency-swift-6-se-0431)
*   [SE-0434: Usability of global-actor-isolated types](concurrency-swift-6-se-0434)

# Effect Polywhatism?

The title of this proposal doesn’t pull any punches. I had to think for quite a bit to really understand what it was trying to say. I wanted to take a little detour to help navigate this.

To get this, you have understand what “effect” means in the context of a programming language. We talk a lot about “types” when working with Swift. But most types, like “Int” or “UIViewController” aren’t sufficient to capture all things a program can do. I always think about types as describing values and instances - things. Effects describe the stuff that could happen while working with those things. That’s not a small set. But, many languages, Swift included, formalize a teeny tiny set of the stuff that could happen. They are often specifically attached to functions.

Here, the two relevant effects that Swift models are errors and concurrency. You can tell these concepts are formalized, because they have built-in support in the language, via the `throws` and `async` keywords. And you can also see how they are integrated into the type system, because both are part of a function’s signature.

If you learned about object-oriented programming, you may have run into the term “polymorphism” before. It just means that one instance could potentially have multiple forms. A `UIViewController` is also an `NSObject`. But here, the multiple forms is not related to the instance type, but the kinds of errors it can produce and how it can be isolated.

Both errors and isolation have been generalized because they now can work with all possible values of these things. That generalization has made those elements polymorphic.

I’m not terribly good at programming language theory. And I’m also not 100% sure isolation is technically considered an effect. But I tried.

Ok, enough of this nonsense.

# The Problem

The `some` keyword is used to hide the implementation type from API clients. It is used all over the place, but is particularly useful for systems that rely on lots of type transformations. Two familiar examples are SwiftUI and Combine. For this to work, the involved protocols need to declare primary associated types. `AsyncSequence` doesn’t do that.

This can result in fragile function signatures that spill your internal abstractions all over the place. They also just look terrifying. I stole this from [an issue](https://mastodon.world/@jonduenas/112424678933077199) related to the problem:

```swift
func notifications(_ name1: Notification.Name, _ name2: Notification.Name) -> AsyncMerge2Sequence<AsyncMapSequence<NotificationCenter.Notifications, Notification.Name>, AsyncMapSequence<NotificationCenter.Notifications, Notification.Name>>
```

😵 This is a non-starter if you are making an API.

There’s also an issue with `AsyncIteratorProtocol` related to correctness. The most natural use of the type doesn’t work in actor-isolated contexts unless it is also `Sendable`. This is rarely the case in practice. An earlier build of Swift 5.10 even detected and warned about this situation. But, it was annoying to address. And because the team knew they were going to fix it anyways, they suppressed the warning. This makes a lot of sense, but the whole thing is definitely not ideal.

A third problem is that an `AsyncSeqeuence` of non-Sendable elements cannot be used when globally-isolated. I kind of glossed over on first read, but then I saw a [question](https://mastodon.world/@jonduenas/112424678933077199) about it. This is one of those confusing things that feels like it should just work.

# The Solution

The proposal addresses all of these problems simultaneously by modifying the API like this:

```swift
protocol AsyncIteratorProtocol<Element, Failure> {
	@available(SwiftStdlib 6.0, *)
	mutating func next(isolation actor: isolated (any Actor)?) async throws(Failure) -> Element?
}
```

This new function makes use of [typed throws](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0413-typed-throws.md) to support the primary associated types. And, it fixes the isolation correctness issue by adding an isolated parameter. Note that parameter type, which was made possible by [SE-0420](concurrency-swift-6-se-0420)! And, if that wasn’t enough on its own, this **also** makes the problem with non-Sendable elements and global actors just go away.

# The Implications

This is the proposal that really makes `AsyncSequence` feel complete. The inability to use `some AsyncSequence` was a major problem for building APIs. I expect we’re going to see much more wide-spread adoption of both it and [AsyncAlgorithms](https://github.com/apple/swift-async-algorithms) because of this.

(Update! I have discovered that `some AsyncSequence` requires the latest OSes. Womp womp.)

The fact that they were able to use isolated parameters to both fix a correctness issue and also make iteration more efficient is just awesome.

Unfortunately, to maintain source compatibility, getting this fix is opt-in for all `AsyncIteratorProtocol` implementations. And, that won’t be pretty if you want to maintain compatibility with Swift 5. I think it’s going to have to look something like this:

```swift
struct MyIterator: AsyncIteratorProtocol {
#if swift(>=6.0)
	mutating func next(isolation actor: isolated (any Actor)? = #isolation) async throws(Failure) -> Element? {
		// get next value
	}
#else
	mutating func next() async throws -> Element? {
		// do the exact same thing here too
	}
#endif
}
```

# Will it Affect Me?

If you have any `AsyncIteratorProtocol` implementations or want to use [AsyncAlgorithms](https://github.com/apple/swift-async-algorithms), for sure. This is going to be a big one for everyone trying to find a way to migrate away from Combine. Though, there are still plenty of ergonomic and functional issues around moving away from Combine completely.

But, I think this is going to help a lot. I’ve been looking forward to it for a long time.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
