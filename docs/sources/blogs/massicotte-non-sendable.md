# Non-Sendable types are cool too you know

Jul 30, 2024

`Sendable` gets talked about a lot. And while it is a critical aspect of Swift concurrency, I think non-`Sendable` types are very interesting and just as important. They are often seen as a problem when facing concurrency issues. But, non-`Sendable` types can actually sometimes be a perfect solution.

Let’s take a look! But, before we do I want to make sure you know what you’re getting into here. This is not introductory material.

## Thread-Safe?

I want to start with something that I think confuses a lot of people. Regardless of what languages they use, programmers have some mental model of what “thread-safe” means.

Here’s what the documentation for `Sendable` says:

> A thread-safe type whose values can be shared across arbitrary concurrent contexts without introducing a risk of data races.

Ok, that sounds pretty unambiguous. But, here’s something weird. Global actor isolated-types implicitly conform to `Sendable`. This means that `UIView`, which is `MainActor`-isolated, is also `Sendable`. Would you consider that type thread-safe? Let’s check its documentation:

> Manipulations to your app’s user interface must occur on the main thread.

I was hoping to find something along the lines of “this type is not thread-safe” to really drive home the point. But, this still sure doesn’t sound like something that can be shared across arbitrary concurrent contexts. To me, “thread-safe” means safe to use from any thread at any time. So what’s going on?

Well, the thing is `UIView` actually **does** meet this definition of thread-safety, but **only** when used with Swift 6. And that’s because the compiler can a) understand its main thread-only requirement and b) strictly enforce it.

The reason “thread-safety” is mentioned so prominently for `Sendable` is because the language is able to achieve the same effect. But, I think this is a confusing thing for people learning about Swift concurrency. Even worse, `@unchecked Sendable` types are intentionally stepping outside the bounds of what the compiler can verify. These types **must** be “thread-safe” in a way that matches the meaning of the term outside of the Swift concurrency world.

What I’m really getting at with all this is `Sendable` and the concept of isolation are inseparable.

## What’s Sendable?

`Sendable` is a so-called “marker protocol”. That is a protocol that has no requirements, but instead serves only to describe some semantic quality of the type. A type that is `Sendable` means it can be freely transferred across isolation domains. These types are thread-safe, keeping in mind the meaning of that term in the Swift concurrency world.

## Ok, so what’s non-Sendable?

Non-`Sendable` just means the lack of a `Sendable` conformance. These types are not possible to share across isolation domains. They are **stuck** in whatever isolation domain they get created in. Lots of things are non-`Sendable`.

The Swift 6 compiler is able to, sometimes, safely perform a one-way transfer of a non-`Sendable` type from one isolation domain to another. This can help tremendously with usability, but it does not change the nature of these types. They are still not safe to **share** and the compiler will not permit it.

It might surprise you to hear me say this, but non-`Sendable` types are **also** thread-safe. That’s because the compiler forces you to use them in a thread-safe way. In fact, all code built with the Swift 6 language mode is thread-safe.

## Protocols

One area that consistently causes people problems is when protocols and isolation meet. Because isolation is a property of all types, protocols necessarily define their isolation requirements too. And sometimes that’s just not what you want.

```swift
protocol NonIsolatedProtocol {
	func someFunction()
}

@MainActor
class MyClass: NonIsolatedProtocol {
	private var state = 0

	// ERROR here
	func someFunction() {
	}
}
```

What’s happening here is the protocol requires that `someFunction` be **non-isolated**, but the type is isolated to a global actor. This conflict is a common example of a very well-known type of problem called [protocol conformance isolation mismatch](https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/commonproblems#Protocol-Conformance-Isolation-Mismatch).

## Removing isolation

There are many ways of dealing with isolation mismatches. One of the most straightforward options is just to remove isolation using the `nonisolated` keyword. This selectively opts-out of any isolation being applied to the whole type.

```swift
@MainActor
class MyClass: NonIsolatedProtocol {
	private let state = 0

	nonisolated func someFunction() {
		// ERROR here now because `self` is still MainActor
		print("my state is:", state)
	}
}
```

Except when you do this, you’re often just kicking the can down the road. You can now conform to the protocol, but the implementation can’t be what you want. Not particularly useful.

This is a contrived case, but I want to highlight something. We removed isolation from just the protocol’s method. If instead we remove the isolation **entirely**, everything works. There’s absolutely nothing about the internals of this object that requires isolation. But, if there was, the compiler would immediately complain about it. Remember, the language does not allow you to make mistakes!

Now here’s where I make a bold assertion: if you **can** remove isolation from a type, you **should**.

Isolation is a **constraint** so removing it makes things more flexible. Here’s the solution to the above problem with all isolation removed. It just looks normal.

```swift
protocol NonIsolatedProtocol {
	func someFunction()
}

class MyClass: NonIsolatedProtocol {
	private var state = 0

	func someFunction() {
		print("my state is:", state)
	}
}
```

The reason this is such a great solution is because it addresses the **root problem**. The definition of `NonIsolatedProtocol` has made promises that `MyClass` cannot keep. Inappropriate isolation, either too much or not enough, can be **detrimental** to a design.

## Where did the isolation go?

Many people get worried when someone suggests removing isolation. Even the keyword “nonisolated” makes people nervous. And I think that’s understandable, because it kinda sounds like it could be unsafe.

But, that’s really not the case. A non-`Sendable` type still must be isolated somehow. Everything always has some well-defined isolation. That problem has just been pushed up a level to the clients of the type. This object is going to get created in some isolation domain and it’s going to **stay there**. It cannot move, because that’s something only `Sendable` types can do.

(I do want to acknowledge that over-isolation can actually help to catch an important class of problem: interoperability with incorrectly-annotated code. This is an inherently difficult thing to handle. But, I do want to call this out because I’m not sure I fully understood this problem until recently.)

## non-`Sendable` + `async`

If there is one **gigantic red flag** that I see all the time, it is non-`Sendable` types with `async` methods.

```swift
class MyClass {
	private var state = 0

	func someAsyncFunction() async {
		print("my state is:", state)
	}
}
```

To understand why this is problematic, you have to understand how non-isolated async functions work. They always run on the global executor. Or, to put it another way, non-isolated async functions always run in the background.

Let’s look at a call site.

```swift
@MainActor
class Client {
	// isolated to the MainActor...
	let instance = MyClass()

	// ... this is MainActor too...
	func useInstance() async {
		// error: requires instance be non-isolated!
		await instance.someAsyncFunction()
	}
}
```

We know that `someAsyncFunction` must run in an non-isolated context. We also know that `instance` is non-`Sendable`. And this means to call this method, `instance` must **already** be non-isolated. We’ve made a type that is, by definition, only usable from non-isolated contexts. This is valid, but probably not what you want.

## A solution?

When I first encountered this problem, here’s what I did to solve it.

```swift
class MyClass {
	private var state = 0

	@MainActor
	func someAsyncFunction() async {
		print("my state is:", state)
	}
}
```

I knew wanted a non-isolated type so I could conform to non-isolated protocols. But, I also wanted async methods. And the only way I could figure out how to do that safely was to apply some isolation. But, this is actually just another side of the same coin. Now, this method is only callable if the instance was **already** on the MainActor.

Can we do better?

## A solution!

Yes, in fact we can. But don’t let the signature intimidate you.

```swift
class MyClass {
	private var state = 0

	func someAsyncFunction(isolation: isolated (any Actor)? = #isolation) async {
		print("my state is:", state)
	}
}
```

What we’re doing here is using an [isolated parameter](/isolated-parameters) combined with some [fancy new Swift 6 features](/concurrency-swift-6-se-0420) to inherit isolation at the callsite. It’s a lot. But this allows our function to be fully general over all possible isolation. This can be used from the `MainActor`, regular actor types, and also a non-isolated context. You don’t even have to interact with the `isolation` parameter. Its mere **presence** establishes the isolation behavior we want.

```swift
@MainActor
class Client {
	// isolated to the MainActor...
	let instance = MyClass()

	// ... this is MainActor too...
	func useInstance() async {
		// ... and now this function will be as well!
		await instance.someAsyncFunction()
	}
}
```

Note the lack of the `isolation` argument. That’s handled by the default `#isolation`.

The isolated parameter makes it possible for non-`Sendable` types to participate in concurrency much more easily. And as a bonus, this is **guaranteed** not suspend on function entry. Later calls within `someAsyncFunction` can still suspend. But, this opens up a little synchronous window and that can be critical for solving certain kinds of concurrency problems.

**Update**

Making an isolated parameter optional turns out to come with some more complexity. But I did not realize this because of a [compiler bug](https://github.com/swiftlang/swift/issues/77301). None of this is “wrong”, and making it non-optional means the `#isolation` default no longer works. So, there are big trade-offs here. But, the safest, most-annoying option actually looks like this:

```swift
class MyClass {
	private var state = 0

	func someAsyncFunction(isolation: isolated any Actor) async {
		print("my state is:", state)
	}
}
```

I want to call this out, but I still think that for the most part, using the optional here makes sense. It’s easier, it’s convenient, and once that bug is fixed it will no longer allow any unsafety.

## `@isolated(any)`

I think **virtually all** non-`Sendable` types should use this isolated parameter technique for their async functions. But, it’s incredibly verbose. And that got me thinking about the relationship between this and [`@isolated(any)`](/concurrency-swift-6-se-0431).

I think it would be really cool if we could instead write this instead:

```swift
class MyClass {
	private var state = 0

	@isolated(any)
	func someAsyncFunction() async {
		print("my state is:", state)
	}
}
```

Today, `@isolated(any)` can only be used with closures. Which, interestingly can also themselves have isolated parameters. But, the more I think about it, the more it seems like isolated parameters and `@isolated(any)` are solving the same problem. Am I wrong?

(Future me: yes, I am wrong! This attribute is a frequent source of confusion. There *could* still be some kind of idea here, but this mostly doesn’t make sense.)

Anyways.

## You should be using non-`Sendable` types

I think non-`Sendable` types are tremendously useful. They are much easier to use with protocols. They are just as “thread-safe” as an isolated type. And now we have a way for them to have usable async methods. There is a [small hole](https://forums.swift.org/t/closure-isolation-control/70378) in their concurrency story. But, overall I think they can be a really powerful tool for modelling mutable state that can work with arbitrarily-isolated clients.

Non-Sendable types are great and you should use them!

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
