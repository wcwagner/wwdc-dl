# Swift Isolation Intuition

To use Swift concurrency successfully, you have learn to think in terms of [isolation](https://www.massicotte.org/intro-to-isolation). It is the foundational mechanism the compiler uses to reason about and prevent data races. All variables and functions have it. The thing is, isolation is really different from every other synchronization mechanism I’ve used before. Now that I have more practice, I find it often feels really natural. But getting to that point took real time! And, boy, did I make some spectacular mistakes along the way.

Developing intuition around how isolation works is essential, but it will be less work than you might think!

## Self

Let’s start by looking at the variable `self`. It’s familiar! You may feel very comfortable with `self`, but there is actually a lot going on.

```swift
func topLevelFunction() {
	self // ERROR: Cannot find 'self' in scope
}
```

The `self` variable is only available in the bodies of methods of a type.

```swift
struct Person {
	let name: String

	func whoAmI() {
		print(self.name)
	}
}
```

Did you ever stop to think where `self` actually comes from? The function `whoAmI` takes _zero_ arguments. I don’t know how Swift has implemented this internally. But, we can model it with a top-level function like this:

```swift
func person_whoAmI(_ instance: Person) {
	print(instance.name)
}
```

It’s not nearly as nice, but this version is roughly equivalent. In fact, many C APIs do exactly this to emulate the concept of objects. Like many other languages, Swift has added syntax **and** a little magic to make it easier for you to work with structures. And you are probably very comfortable with both of these things!

You can start by thinking about isolation the same way you think about `self`.

## Isolated Parameters

It’s possible for you to make pretty extensive use of Swift concurrency without ever even running into [isolated parameters](https://www.massicotte.org/isolated-parameters). Here’s a simple example of what the syntax looks like:

```swift
func usesIsolatedParams(_ actor: isolated any Actor) {
	print("I'm isolated to \(actor)")
}
```

Yes, the type of `actor` is quite complex. But, I really want you to try to focus instead on the shape of the function. It is really similar to `person_whoAmI` from above. It is just a function that takes a parameter! While it might not be common to do isolation this way, I think it’s really interesting to see it laid out so explicitly.

I also want you to note the `actor` parameter, which defines the isolation of the function, **cannot change** within the body. This is an important thing to realize about isolation in general. It will never change for synchronous code.

## Async

I tried to pick my words really carefully there. Isolation never changes for **synchronous** code, but it can **temporarily** change when you make asynchronous calls via `await` or `async let`.

```swift
func usesIsolatedParams(_ actor: isolated any Actor) async {
	print("I'm isolated to \(actor)")

	// all synchronous, so no isolation changes will occur
	stuff()
	things()
	work()

	// but this may require a change in isolation!!
	await someAsyncFunction()

	print("back to \(actor)")

	// may also require a change!
	async let value = anotherAsyncFunction()

	print("and back again to \(actor)")
}
```

Isolation cannot change at all for a **synchronous** function. And it cannot change for the **synchronous parts** of an async function. But, as soon as you need to make an async call, it could.

This is really a consequence of the fact that isolation is controlled entirely by a function’s definition. It does not matter how the caller is being isolated. This is completely different from how queues or locks work, and its worth taking a moment to think about it.

Once you’ve digested this, we can distill everything down into two rules:

**Rule 1**: isolation is controlled by definitions

**Rule 2**: isolation can only change via async calls

## Tracing isolation

**Update**: SwiftUI has been changed as of the SDKs within Xcode 16! This section was written when View only applied `@MainActor` to `body`. Please keep that in mind!

Rule 2 governs how isolation can and cannot **change**. Rule 1 controls where isolation is **specified**. And, yes, that rule _sounds_ simple. But the most common form of isolation, global actors like `@MainActor`, can influence a definition when protocols and/or inheritance are involved. And since those are often in other files/modules, it isn’t always obvious.

To illustrate this, I’m going to use SwiftUI. I am [not a fan](https://www.massicotte.org/swiftui-isolation) of how SwiftUI’s `View` type handles isolation. But, `View` is something many Swift developers are familiar with, and it is precisely because it is so tricky that it makes for great example material.

```swift
struct MyView: View {
	var body: some View {
		Text("hello: \(self)") // what is the isolation here?
	}
}
```

Hey look, a `self` reference! It might not take you much effort to understand what `self` is **now**. But, there was a point in **everyone’s** programming journey when they had to do quite a bit of thinking to get it.

Isolation is the same thing!

If you feel good about how `self` works, it’s because you’ve internalized the algorithm the compiler uses. So much so, that you might not even need to think about it. But I’m going to really spell out what’s happening with isolation here, despite it being so similar.

Let’s bring the definition of `View` in too, so we can look at it all together. Remember, our objective is to determine the isolation of the `body` property.

```swift
protocol View {
	associatedtype Body : View

	// 4 - protocol member ... AH HA!
	@ViewBuilder @MainActor
	var body: Self.Body { get }
}

// 3 - protocol conformance
// 2 - type
struct MyView: View {
	// 1 - definition
	var body: some View {
		// what is the isolation here?
		Text("hello \(self)") 
	}
}
```

There’s a lot going on here, so let’s break it down one step at a time.

1.  First, we check the `var` definition. Nothing.
2.  Next, we check the type definition. Still no isolation.
3.  Ok, does this `var` satisfy a protocol? We have to check that.
4.  Here it is! This protocol defines `body` as `MainActor`-isolated.

## Global actor inference

This whole process is quite involved because of something called global actor inference. This [article](https://www.hackingwithswift.com/quick-start/concurrency/understanding-how-global-actor-inference-works) does a great job of explaining the rules in more depth. But I’m going to try to boil it all down into one really simple rule:

**Rule 3**: protocols can specify isolation

In the case of `View`, the protocol is specifying the isolation of a specific member. But it is possible to apply isolation to the protocol as a whole. I want to highlight this because, at first, I was confused about how it worked.

```swift
@MyCustomNonMainGlobalActor
protocol CustomActorStuff {
	...
}

// This does not affect the isolation of the UIViewController
// type. It's still MainActor...
extension UIViewController: CustomActorStuff {
	// ... but everything in here will be inferred
	// to use MyCustomNonMainGlobalActor
}
```

This is really just another consequence of rule 1: the definition **wins**. While a protocol can specify isolation, you cannot use one to change it.

## The algorithm

The whole point here is to help you develop some intuition about how things get isolated. To do that, we’re just learning the algorithm the compiler uses. And yes, it can get complex with inheritance or protocols. But, the actual algorithm your brain can use can be very simple.

*   Check the definition
*   Check the enclosing type
*   Protocol involved?
    *   Check its definition
    *   Check its enclosing type

That’s it.

All in all, I find global actor inference to be something that only sounds scary and complex. In my experience, it is usually something you can learn once and then just apply.

`View.body` is `MainActor`, done.

## Again, without the inference

I want to help solidify how this process works by looking again a SwiftUI `View`. But, this time, we’re going to consider two trickier cases.

```swift
// 3 - protocol conformance
// 2 - type
struct MyView: View {
	var body: some View {
		// we know this is MainActor
		Text("\(formalGreeting) \(self)") 
	}

	// 1 - definition
	func formalGreeting() -> String {
		// but what about this?
		return "hello"
	}

	func lessFormalGreeting() async -> String {
		// or this???
		return "sup"
	}
}
```

Because SwiftUI’s `View` only isolates `body`, tracing the isolation of these two functions is more straight-forward.

For `formalGreeting`:

1.  The definition has no isolation.
2.  The enclosing type has no isolation.
3.  The View protocol doesn’t impact the function.
4.  ???

So, nothing? Yes! Non-isolation is totally a thing, and in fact is quite common. But, rule 2 still applies! Synchronous code cannot change isolation. So, this function just has no isolation at all. Fortunately, the compiler has our back here and will prevent us from doing anything unsafe accidentally.

Now, what about `lessFormalGreeting`? The only thing we’ve changed is we made the function `async`. But the algorithm still works! This function is also non-isolated. Making a function async does not change how you determine isolation.

## Closures

There’s one more thing we need to cover. When it comes to isolation, closures are extremely close in behavior to regular functions. Rules 1 and 2 still apply. Rule 3 isn’t even relevant because closures cannot conform to protocols. But we do have a problem. When working with concurrency you may make use of the `Task` API. And it, being part of the currency system, treats closures specially too.

Let’s modify our view from above. We want to determine what isolation will be in effect for the `Task` body.

```swift
struct MyView: View {
	var body: some View {
		// we know this is MainActor
		Text("\(formalGreeting) \(self)")
	}

	func formalGreeting() -> String {
		Task {
			// ...ummmm...
		}
	}
}
```

Figuring out how `Task` does isolation starts with first knowing the isolation of the enclosing callsite. We know how to do this now, we just use The Algorithm.

*   `formalGreeting` has no isolation
*   `MyView` has no isolation
*   Does `View`’s isolation of `body` apply?

We can see that `formalGreeting` is called from `body`, and we know that is `MainActor`-isolated. But, it’s really important to keep in mind that isolation is a **compile-time** construct. The **runtime** state does not matter. This means `formalGreeting` is **non-isolated**, even if it will actually only ever run on the `MainActor` in practice. But we need to know more to figure this all out.

`Task`’s parameter definition is a little magic. The closure that `Task` takes uses a special attribute called [`@_inheritActorContext`](https://github.com/apple/swift/blob/main/docs/ReferenceGuides/UnderscoredAttributes.md#_inheritactorcontext). This changes the definition of the `Task` body to inherit whatever isolation is in effect on the outside. This means the isolation outside a `Task` **does not change** on the inside. And that’s great, because it does not alter our algorithm at all!

All this long, dense explanation means is `Task` will match the isolation of its enclosing function. In this case, that makes its body non-isolated.

The same thing, however, is **not** true of `Task.detached`.

```swift
struct MyView: View {
	var body: some View {
		// we know this is MainActor
		Text("\(formalGreeting) \(self)")
	}

	@MainActor
	func formalGreeting() -> String {
		Task.detached {
			// ...soooo...
		}
	}
}
```

I’ve made two changes to the code. I’ve added explicit isolation to `formalGreeting`, but I’ve also switched to using `Task.detached`. This API will prevent isolation inheritance.

Despite that `@MainActor` on the containing function, this `Task` will be non-isolated.

## Explicit Closure Isolation

I want to mention just one more detail about closures. Because they are basically a function + a definition all in one, closures have another capability. You can also define isolation inline.

Check this out:

```swift
struct MyView: View {
	var body: some View {
		// we know this is MainActor
		Text("\(formalGreeting) \(self)")
	}

	func formalGreeting() -> String {
		Task { @MainActor in
			// ...okaaay...
		}
	}
}
```

In this example, `formalGreeting` is back to being non-isolated. And we know that `Task` will also be non-isolated via inheritance. But then we go ahead and add explicit isolation on top of that! Does this work?

Recall rule 2: isolation can only change via async calls.

This change in isolation is **not** a violation of this rule, because `Task` allows us to introduce a new async context! But, to really highlight that, look at an example that does not use `Task`:

```swift
// a non-isolated function
func takesAClosure(_ block: () -> Void) {
	// definitely not running on the MainActor
	block()
}

func usesClosure() {
	// WANRING: Converting function .... loses global actor 'MainActor'
	takesAClosure { @MainActor in
		// wait, why not?
	}
}
```

Our **closure definition** says it is `MainActor`-isolated, but the **parameter definition** does not. The compiler correctly catches this mis-match. There’s nothing async about this, so a change in isolation is not possible.

The take-away here is the `Task` API is special. But it is special in a way that I think ends up making it feel surprisingly natural.

(I also want to point out that closures may be getting [more powerful and less-weird](https://github.com/sophiapoirier/swift-evolution/blob/closure-isolation/proposals/nnnn-closure-isolation-control.md) in Swift 6.)

## Practice makes better

I went though several variations of this post. And it got way longer than I was originally expecting. After stumbling onto the `self` analogy, I really thought it could be a good way to help develop intuition around isolation. But, like all good analogies, this one breaks down when you look closely. There are lots of places where `self` and isolation do not behave even remotely the same.

Despite the weaknesses, I think the concepts here still have merit. Learning how `self` works seems to be something people can make second nature. And I think the same thing can be done for isolation. It’s just going to take some practice. I really hope this approach is helpful. But, if it isn’t or is confusing at all, please let me know.

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
