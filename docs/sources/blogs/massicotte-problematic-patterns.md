# Problematic Swift Concurrency Patterns
Oct 29, 2024

Recently, someone asked me about best practices when using Swift concurrency. I have mixed feelings about the concept of a “best practice”. I’ll get to that in a bit. But, in this case, I said that the technology is still very young and we’re all still figuring it out.

But, I then went on to say that I have now come across a number of techniques that often **don’t** work out. This does not mean bad! It just means that I see them a fair bit, and they often end up being a problem. I thought it could be useful to collect and share what I’ve seen.

## “Split Isolation”

This is a term I’ve come up with for a type that uses more than one isolation domain internally.

```swift
class SomeClass {
	// non-isolated
	var name: String
	
	@MainActor
	var value: Int
}
```

A type like this is problematic, because half of it is non-isolated, and half is `MainActor`-only. But, that’s really weird! Because this type isn’t `Sendable`, if you were to ever create one off of the `MainActor`, it could never be later moved back to the `MainActor`, making `value` inaccessible.

There **might** be advanced/clever usages of such a type. But I think the vast majority of the time, a global actor should be applied to the type as a whole, not to individual properties.

## `Task.detached`

I see `Task.detached` all over the place. And this makes sense, because it is a very convenient way to get stuff off the `MainActor`.

```swift
@MainActor
doSomeStuff() {
	Task.detached {
		expensiveWork()
	}
}
```

This **does** work! It also looks really similar to `DispatchQueue.global().async`, so it feels familiar. But, while `detached` does prevent isolation inheritance, it **also** does other stuff too. Detached tasks do not inherit priority or task-local values.

Instead, think about a `nonisolated` function. This is very explicit, not subject to side-effects, and makes it impossible to accidentally forget to remove the actor isolation at all call sites.

```swift
@MainActor
doSomeStuff() {
	Task {
		await expensiveWork()
	}
}

nonisolated func expensiveWork() async {
}
```

I wrote up a [whole thing](https://www.massicotte.org/step-by-step-network-request) that goes into more detail about this kind of stuff, in case you want to check that out too.

## Explicit Priorities

I see people using explicit priorities all the time. It’s not inherently wrong to do this, but it’s really complicated! Priorities can have effects on timing and performance. The system is quite good about preventing it, but it’s also easy to accidentally introduce priority inversions.

I think you should **always** include a comment explaining why the default won’t work.

```swift
// Explain yourself here clearly! Are you sure?
Task(priority: .background) {
	await someNonCriticalWork()
}
```

## `MainActor.run`

I’ve gone into quite a bit of [detail](https://www.massicotte.org/dynamic-isolation) about this one in the past. I think `MainActor.run` is rarely the right solution. Swift concurrency gives you tools to make sure that APIs cannot be used wrong. You should use them! They can keep your code simpler and prevent mistakes.

```swift
// why do this...
await MainActor.run {
	doMainActorStuff()
}

// ... when this will usually work?
await doMainActorStuff()
```

## Stateless Actors

The purpose of an actor is to protect mutable state. That’s what actors do. Yet, I regularly run into actors that have no instance properties. This means they have no state to protect! Usually, this is because you just want to get work off the main thread. And if that is the case, look into a non-isolated async function.

## `@preconcurrency import` with Async Extensions

You’ve got some type you do not control, and it uses completion handler-based APIs. You want to wrap that up with async methods, but that introduces warnings. So, you add a [`@preconcurrency import`](https://www.massicotte.org/preconcurrency) to silence the warnings.

Moving from completion handlers to async methods can change semantics and cause code to run on background threads. Be **really** careful here!

## Redundant `Sendable` Conformances

I frequently see types that look like this:

```swift
@MainActor
class SomeClass: Sendable {
}
```

This is strange, because global actor isolated types **are** `Sendable`. Now, it isn’t wrong to have the redundant `Sendable` conformance. But, I think it can be a sign of confusion/misunderstanding.

## `@MainActor @Sendable` closures

Here’s a type you can run into a lot. It’s a function that will run on the `MainActor`, but also needs to be itself `Sendable`.

```swift
@MainActor @Sendable () -> Void
```

Except, there was a [change](https://www.massicotte.org/concurrency-swift-6-se-0434) in Swift 6. `@MainActor` closures are now `Sendable`, just like all other global actor isolated types. The combination of `@MainActor` and `@Sendable` is still required for Swift 5/Xcode 15 compatibility. But, a plain `@MainActor () -> Void` might be all you need and is much less restrictive.

## RunLoop APIs

There are still quite a few systems out there that must be used with `NS/CFRunLoops`, like `NSTimer` and JavaScriptCore. These will not work correctly with non-`MainActor` concurrency contexts. Typically, you can find a way to make these things work using the main thread.

## Actors + Protocol With Synchronous Methods

Actors are, by their nature, asynchronous. You cannot run synchronous methods on an actor outside of the actor itself. Because of this, making an actor conform to a protocol that has synchronous methods is usually going to be a problem. There are times when you can pull it off, but you’ll want to think hard about whether it makes sense. In many scenarios like this, an actor is just the wrong choice.

## Using Obj-C->Async Translations

The compiler will automatically generate async versions of Objective-C completion handler-based methods. The bad news is, unless the type itself is `MainActor`-isolated or `Sendable`, these translations will be problematic. They won’t be possible to use diagnostic-free without a `@preconcurrency import` and will have different semantics that could make them unsafe.

I would stay away unless you are 100% sure the translation makes sense. And if you cannot see the implementation, that could be impossible to determine.

## Blocking for Async Work

Don’t use `DispatchSemaphore` or `DispatchGroup` to wait on async work. It could be very rare, but you are eventually going to deadlock.

## Too Much Code in Closures

It can be extremely hard to understand the compiler’s concurrency diagnostics. And, because there’s now [code flow analysis](https://www.massicotte.org/concurrency-swift-6-se-0414) happening, reasoning about how or why a diagnostic is being presented can be even more difficult. Keeping the amount of code inside of closures under control can really help narrow down problems.

I also find this really helpful for readability. Win win.

## Unstructured When Structured Would Work

Sometimes, you just need to create a new `Task`, and that’s fine. But, if you can avoid it, you should. Sticking with structured concurrency is usually simpler, allows some automatic cancellation support, and encourages you to define your isolation requirements statically.

## Avoiding non-`Sendable` Types

You can build some pretty useful things with [non-`Sendable` types](https://www.massicotte.org/non-sendable). If they need to participate in concurrency, you may need to make use of isolated parameters, but with a little practice you can get those down.

I want to stress that again, but in a different way. If you are adding async methods to non-`Sendable` types and you are **not** using isolated parameters, things probably aren’t working as you intend. And, you also probably have warnings off because this arrangement almost never works and the compiler will catch it.

## Other Areas

I didn’t come up with this list all by myself. I asked for ideas, and a few things were suggested by others. There were two things that came up a lot, neither of which I feel I can help with that much.

### Testing

Testing code that uses concurrency can be very tricky in some situations. Particularly if you need to start operations that have asynchronous side effects that you cannot directly wait for.

```swift
func hasAsyncSideEffects() {
	Task {
		// these effects are hard to test
	}
}
```

I’m sure this isn’t the only difficult case either. I don’t have any great suggestions here. But, there is a post over at [pointfree](https://www.pointfree.co/blog/posts/110-reliably-testing-async-code-in-swift) with some interesting options.

I’d be very interested in hearing from you if you have ideas/experience here!

### Adopting AsyncSequence

By a wide margin, the most common thing I hear from people is around adopting `AsyncSequence`. This deserves a dedicated post (or three), but I’m kind of a beginner when it comes to reactive programming so this stuff is hard for me.

By no means is using `AsyncSequence` inherently problematic. I have used it successfully, and I have seen many others do so as well. But what I can say for sure is if you are having trouble, you aren’t alone.

Please point me to resources that have helped you! Or to specific stuff that has not worked!

## “Best” practice

It’s useful to know about things that work well. All those pitfalls, edge cases, and details can take a lot of time and pain to discover. But, I also think there can be real danger in blindly following instructions, especially if they come from a trusted source. This can prevent you from trying new things. And new things are how we find then next, more best pratice. Or why that best is actually only ok.

I’ve seen the stuff here work out badly. But, that does not mean you should not use your own judgement. Please keep trying things! And when you do, tell me about how it worked out.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
