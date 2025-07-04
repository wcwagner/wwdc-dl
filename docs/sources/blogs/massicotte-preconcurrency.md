# So how does this whole @preconcurrency thing work?

Oct 14, 2024

I consistently find the `@preconcurrency` attribute to be confusing. But, I’m tired of that. Let’s just, once and for all, get a better handle how to use this thing.

## One Attribute, Many Purposes

Remember, Swift concurrency is all about the type system. This means that **definitions** are hugely important to how things function. The `@preconcurrency` attribute alters how definitions are interpreted by the compiler. In general, it relaxes some rules that might otherwise make a definition difficult or even impossible to use.

It has **three** distinct uses. And while they all apply to definitions, the details are quite different. We’ll cover them all, in increasing order of complexity.

## Preconcurrency Conformance

This is actually a new feature of Swift 6, introduced with [SE-0423](/concurrency-swift-6-se-0423). The whole idea with this one is to provide a simple and safe way to deal with protocol-isolation mismatches. It tells the compiler yes, actually, my isolated type can conform to this non-isolated protocol. It was introduced to help out with protocols that are not **yet** marked with a global actor, but should be.

### Isolation Mis-Matches

Here’s the traditional approach:

```swift
// Defined in some other module
public protocol ViewDelegateProtocol {
	func respondToUIEvent()
}

@MainActor
class MyViewController: ViewDelegateProtocol {
	// step 1, remove the isolation that mis-matches
	nonisolated func respondToUIEvent() {
		// step 2, put it back
		MainActor.assumeIsolated {
			// ...
		}
	}
}
```

This technique still works. And there are times when it remains useful. But, there’s just so much boilerplate. And the non-isolated methods end up exposing an API for your type that’s very easy to use incorrectly. Contrast all that with one single attribute that gives you a very concise and safer option.

```swift
@MainActor
class MyViewController: @preconcurrency ViewDelegateProtocol {
	func respondToUIEvent() {
		// no need for any of that
		// nonisolated/assumeIsolated
	}
}
```

Much nicer!

### Intentionally Non-isolated Protocols

Interestingly, the preconcurrency conformance has another use! It is also handy to conform to a protocol that doesn’t need to be isolated. That is, they are intentionally non-isolated. An example is `NSTextStorageDelegate`. This protocol can be used on any thread/isolation/queue/whatever, as long as you keep it there. This is more or less the same situation as a mis-match, and is just as tricky when used with isolated types.

But, you can use a preconcurrency conformance to make it work.

```swift
@MainActor
class MyViewController: @preconcurrency NSTextStorageDelegate {
	func textStorage(
		_ textStorage: NSTextStorage,
		didProcessEditing editedMask: NSTextStorage.EditActions,
		range editedRange: NSRange,
		changeInLength delta: Int
	) {
		// ...
	}
}
```

I’m the first to admit: this is weird. There’s nothing “pre-concurrency” about this, so it’s a bit of a hack. But, it works well here because as far as the compiler is concerned these two situations are functionally equivalent.

Moving on!

## Working with Swift 5

The next way to use `@preconcurrency` is when you are **making** an API. Here’s the situation. You have a **public** API, originally implemented before Swift 6. Say it looks something like this:

```swift
/// Does the work.
///
/// Will invoke block on a background queue when complete. 
public func doWork(block: @escaping () -> Void) {
	// ... work happens here
}
```

Note that documentation! The `block` closure will be invoked on a background queue. But, the closure is **formed** at the callsite, which probably won’t be in the background. For this API to work, `block` will need to move from wherever it was created to that background queue. And the only types that support this kind of operation must conform to `Sendable`.

This API is very problematic. It cannot be implemented error-free in Swift 6. But worse, it can cause serious runtime issues for a Swift 6 client. This is because it is doing something internally that its definition doesn’t actually allow.

You do not have to move the module to Swift 6 to fix this though. You can just address the signature. Let’s fix that by making this closure `@Sendable`.

```swift
public func doWork(block: @escaping @Sendable () -> Void) {
	// ... work happens here
}
```

With this change, we can address the externally-visible problems now, and set ourselves up for moving to Swift 6 internally. But we’ve also introduced a surprising effect! Take a look at what will happen to Swift 5 mode clients:

```swift
doWork {
	// warning: capture of 'nonSendableType' with non-sendable type 'NonSendable' in a `@Sendable` closure
	print(nonSendableType)
}
```

This occurs even if that Swift 5 client has concurrency warnings **disabled**! This surprises a lot of people, understandably so. What’s going on?

Well, the compiler doesn’t allow you to suppress warnings for concurrency features you are **actively** using. This client is actively using the API, and it requires a `@Sendable` closure. So, the compiler enforces that, even if they don’t want to see these diagnostics.

Would you like to guess what the solution is?

```swift
@preconcurrency
public func doWork(block: @escaping @Sendable () -> Void) {
	// ... does the work
}
```

Applying `@preconcurrency` like this effectively conditionalizes the concurrency features you’ve used in your definition. If the client is in a “pre-concurrency” mode, the warnings will be suppressed. If not, they’ll be shown.

This works for more than just `@Sendable` too. It can also be used to conditionalize global actor isolation. Check out how SwiftUI uses it.

```swift
@MainActor
@preconcurrency
public protocol View {
	// ...
}
```

Preconcurrency APIs are also ABI-compatible. Adding annotations can change the binary interface for APIs, but built clients will still work correctly without needing to be re-built against the updated library. This is very important for Apple, but I doubt it will be too useful for most 3rd-party developers.

## Working with Swift 6

The last use of this attribute is the thing everyone tries when they run into a concurrency error they do not understand: `@preconcurrency import`.

I believe this construct is confusing for three reasons. First, it’s hard to form a good mental model of what kinds of problems a preconcurrency import can address. Second, it isn’t always clear **why** a diagnostic is being presented. So even with a solid understanding, it can sometimes be tough to reason about how preconcurrency could change things. And third, I’m sorry to report that there have been a number of bugs around the `@preconcurrency import` implementation that make the whole thing significantly harder to learn.

We’re going to overcome all of these things! Mostly!

A good way to think about an `@preconcurrency import` is you are telling the compiler “I’m using this API correctly, it’s just missing annotations”. Now remember that we’re working with imports, so there always has to be at least two modules involved. That makes examples a little more complex.

### Non-Sendable Types

```swift
// module A
class NonSendable {}

func returnNonSendable() async -> NonSendable {
	NonSendable()
}

// client
import ModuleA

// error: Non-sendable type 'NonSendable' returned by implicitly asynchronous
// call to nonisolated function cannot cross actor boundary
let value = await returnNonSendable()
```

A non-isolated async function means it will run in the background. But, this function is attempting to create a non-`Sendable` type in the background and pass it to the caller. This will almost never work. Yet, it is an **extremely** common pattern, particularly with Objective-C-to-async translations.

But maybe this `NonSendable` type just hasn’t been marked `Sendable` **yet**. Or maybe this **specific** usage pattern is safe.

An `@preconcurrency import` will address this kind of problem. And, making it easier, the compiler realizes this and will prompt you to add the `@preconcurrency` attribute.

(See the `sending` keyword and [SE-0430](/concurrency-swift-6-se-0430) for ways to better express this particular example.)

### Non-Sendable Closures

Here’s another example I think is super-interesting. Suppose you are using a protocol from an external module, like this:

```swift
// module A
public protocol Working {
	func doWork(block: @escaping () -> Void)
}

// client
import ModuleA

class MyClass: Working {
	func doWork(block: @escaping () -> Void) {
	}
}
```

Only, here’s the thing. You know, from reading documentation, that this callback can be invoked on any thread. That means it has to be `@Sendable`, kinda like what we saw earlier. Except that’s not how the protocol is defined. And if you add a `@Sendable` annotation, you no longer match the protocol. This can make it very hard to implement the conformance how you’d like.

You can fix this with `@preconcurrency`!

```swift
@preconcurrency import ModuleA

class MyClass: Working {
	// compiler will accept this slight mis-match
	func doWork(block: @escaping @Sendable () -> Void) {
	}
}
```

This is also a situation where the compiler will realize the problem and suggest you use a `@preconcurrency import`.

### Hazards

There’s something I think you need to keep in mind when using a preconcurrency import. You are telling the compiler that it should ignore these missing `Sendable` conformances. You are saying that everything is fine. But, you could be wrong! It’s possible that what you are currently doing actually isn’t safe. “Swift 6 mode with no errors” is not the same thing as correct.

And, in my experience, documentation is pretty hit-or-miss in these areas. Sometimes it is clear how to use an API correctly, but not always. And when things are ambiguous it can be very hard to be sure what to do. Worse, a preconcurrency import applies to the entire file. This makes it fairly easy to accidentally hide a real problem in one spot while intentionally addressing something else.

Pay attention closely here, because it’s easy to build a system that is dependent on a particular type being `Sendable`. Finding out after you built the thing that some type you do not control is actually not `Sendable` isn’t great.

I also wanted to specifically highlight this bit of code. You might think you can get clever here like this:

```swift
@preconcurrency import var SomeLibrary.ActuallySafeGlobal
```

I’m afraid to report that while this looks cool, it (currently, anyways) [does not work](https://github.com/swiftlang/swift/issues/74518).

## Wrapping Up

One attribute, three distinct uses. Sure, they are all closely-related, but it’s a lot.

Personally, I find the preconcurrency conformance to be pretty clear. It’s very easy to identify the situation. I don’t love using it as a workaround for protocols that are supposed to be non-isolated. But, I’m optimistic that we’ll see some improvements in this area over time.

I have noticed something funny about annotating APIs with `@preconcurrency`. It makes me kinda nervous! It really highlights how easily a pre-Swift 6 mode client can use things wrong. But, that’s just the nature of pre-Swift 6 code. Plus, it’s a good reminder to keep your docs up to date, even if we can now encode this information directly into the type system as well.

And, I think the situation with preconcurrency imports has gotten better. The compiler seems to be quite good about suggesting it when it could help. But, it definitely comes with very sharp edges. It allows you to paper over problems that could have a profound impact on your design. You can definitely use preconcurrency import, but you should do so with care.

***

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
