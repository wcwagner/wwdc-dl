# SE-0434: Usability of global-actor-isolated types
Jul 11, 2024

Global actors are central to the vast majority of Swift programs. In fact, often you only really need two kinds of isolation - `MainActor` and not-`MainActor`. But, global actors have some quirks that makes for some strange/frustrating behavior.

This [proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0434-global-actor-isolated-types-usability.md) is kind of a grab bag that improves them in three ways.

Index:

*   [SE-0401: Remove Actor Isolation Inference caused by Property Wrappers](https://www.massicotte.org/concurrency-swift-6-se-401)
*   [SE-0411: Isolated default value expressions](https://www.massicotte.org/concurrency-swift-6-se-411)
*   [SE-0414: Region based Isolation](https://www.massicotte.org/concurrency-swift-6-se-0414)
*   [SE-0417: Task Executor Preference](https://www.massicotte.org/concurrency-swift-6-se-0417)
*   [SE-0418: Inferring Sendable for methods and key path literals](https://www.massicotte.org/concurrency-swift-6-se-0418)
*   [SE-0420: Inheritance of actor isolation](https://www.massicotte.org/concurrency-swift-6-se-0420)
*   [SE-0421: Generalize effect polymorphism for AsyncSequence and AsyncIteratorProtocol](https://www.massicotte.org/concurrency-swift-6-se-0421)
*   [SE-0423: Dynamic actor isolation enforcement from non-strict-concurrency contexts](https://www.massicotte.org/concurrency-swift-6-se-0423)
*   [SE-0424: Custom isolation checking for SerialExecutor](https://www.massicotte.org/concurrency-swift-6-se-0424)
*   [SE-0430: `sending` parameter and result values](https://www.massicotte.org/concurrency-swift-6-se-0430)
*   [SE-0431: `@isolated(any)` Function Types](https://www.massicotte.org/concurrency-swift-6-se-0431)
*   SE-0434: Usability of global-actor-isolated types

# The Problem

### Implicitly Non-Isolated Properties

The compiler gets pretty clever with the properties of globally-isolated types. If they are `Sendable`, the compiler treats them as non-isolated within its defining module. It knows that because they are `Sendable`, they are actually safe to use from any domain. Enforcing the isolation serves no safety purpose. This is pretty smart, and helps to loosen restrictions. Thing is, it currently only works for `let` in value types.

```swift
@MainActor
struct SomeMainActorType {
	let x: Int
	var y: Int

	nonisolated func readValues() {
		print(x) // this is allowed!
		print(y) // this is not?
	}
}
```

### Closures

It took me a long time to fully understand that a globally-isolated type **becomes** `Sendable`. Once you apply isolation, the compiler has enough information to keep things safe in all circumstances. In fact, this rule is stated explicitly in [SE-0316](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0316-global-actors.md):

> A non-protocol type that is annotated with a global actor implicitly conforms to `Sendable`.

However, this isn’t actually true for closures.

```swift
let closure = { @MainActor in
	// capture a bunch of non-Sendable stuff
}

Task {
	// Error: capturing non-Sendable `closure`
	await closure()
}
```

The only workaround is also make them `@Sendable`, and this **severely** impacts their usability.

```swift
let closure = { @Sendable @MainActor in
	// now can capture only Sendable stuff 😖
}
```

### Subclassing

Finally, a restriction was added to Swift 5.10 to catch a potential unsafe pattern around subclassing.

```swift
class NotSendable {}

// error: main actor-isolated class 'Subclass' has different
// actor isolation from nonisolated superclass 'NotSendable'
@MainActor
class Subclass: NotSendable {}
```

But it turns out the problem here isn’t the isolation itself. This has exactly the opposite issue of closures. It is the implicit `Sendable` that comes along with the global actor that allows the unsafe behavior.

# The Solution

The fixes for the first two of these problems are straightforward.

The compiler is going to get even smarter about how it enforces isolation on `Sendable` properties of value types.

```swift
@MainActor
struct SomeMainActorType {
	let x: Int
	var y: Int

	nonisolated func readValues() {
		print(x) // this is allowed!
		print(y) // this is now also ok!
	}
}
```

Second, globally-isolated closures are now `Sendable`!

```swift
let closure = { @MainActor in
	// capture a bunch of non-Sendable stuff
}

Task {
	await closure() // now ok! 🙌🏻
}
```

The fix for the subclassing problem is a little strange. A globally-isolated subclass will now be allowed, but will it will no longer get an implicit `Sendable` conformance.

# The Implications

In all three of these situations, you may have workarounds in place that are just no longer necessary. I don’t think I’ve hit the other two issues myself, but the closure change here is a big deal. I have encountered this in numerous situations and it was always painful.

I think it’s **a little** weird that we now have this exception to global-actor-means-sendable rule. It feels like quite a corner-case to me. I imagine this situation doesn’t come up a lot, but could probably help with migrating pre-Swift 6 code? I’m not sure.

# Will it Affect Me?

I’d classify this as mostly a bug fix-style proposal. It’s cool to see the compiler getting smarter about value types. I also don’t use subclasses myself, and I have kinda mixed feelings about the new exception. I guess it must be useful to someone?

For me, the most exciting change is around closures. I would be surprised if you have done significant work with Swift concurrency and have **not** been affected by this. It’s wonderful to see this restriction lifted. Yet more situations where `Sendable` is not required!

# Wrap Up

My original goal was to finish all of these *before* WWDC. I missed, but hey I wasn’t too far off! On top of that, there actually is another proposal, [SE-0428](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0428-resolve-distributed-actor-protocols.md), related to distributed actors. Do check that out if this interests you, but I’m calling it here. This was a lot of work.

Going through these proposals was incredibly educational for me. I learned way more about each than I probably ever would have otherwise. But, one central theme really stood out. Yes, the language has made enormous strides in improving data race safety. Yes, lots of new syntax and complexity has been introduced. But, for the most part, things have just gotten transparently better. The majority of all this developers will never need to understand. If you are going deep with concurrency in your project, there’s so many more tools. And if you aren’t, Swift 6 makes it way easier to side-step the whole thing.

I still don’t feel like I have a good read on how Swift 6 language mode adoption is going. It **seems** like lots of smaller projects are having success. I’m quite curious how the process is going for larger projects/teams. I’m particularly interested in seeing the impact on Apple’s own APIs. I expected a lot more deprecations than we got.

For now, I cannot wait for Swift 6/Xcode 16 to be out of beta. I’m already finding the Swift 5.10 compiler incredibly limiting. There are a lot of new features and capabilities I’m having a hard time living without. It’s just a lot better.

---
[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](https://www.massicotte.org/about) if you think I could help.
