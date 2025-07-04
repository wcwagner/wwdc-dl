# Concurrency Step-by-Step: Reading from Storage

Nov 30, 2024

Not too long ago, I was re-reading an “introductory” [post](/intro-to-isolation) I wrote. Honestly, I could barely make it though. I guess a big part was my own defintion of “introduction” when it comes to concurrency has been evolving. As I was reading, I kept imagining a true beginner doing the same thing. It’s embarrassing! I’m not going to remove it, but I don’t feel great about it.

I still do think it is absolutely vital that more effort be directed towards people getting started. More now than ever. All this inspired me to finally finish up this post, which has been in the works for a while now.

A theme that comes up over and over with Swift concurrency is trying to “keep the compiler happy”. You just want the stupid errors to go away. While trying to make that happen, you stumble across a number of things, like `Sendable` or [`@preconcurrency`](/preconcurrency). You might even start changing `class` to `actor` and how different could that possibly be, it’s even the same number of characters. So you just start throwing syntax at the problem. This is understandable!

It can *sometimes* even work in the short term. But this path usually leads to frustration and anger. It will often produce extremely complex designs that just lead to yet more problems.

Welcome to the second installment of “Swift Concurrency Step-by-Step”. The purpose of these posts is to work through a common task to help build up a real understanding of what is going on. Last time, we looked at a [network request](/step-by-step-network-request). This time, we’re going to load a model from a data store.

## Quick notes

*   I’m going to ignore error handling to keep things focused
*   I’m not very good at SwiftUI
*   This stuff **requires** Xcode 16 or later

I had a really hard time dreaming up an example that would both be simple and also illustrate the problem. I think local storage will work well, but we’re going to have to keep it quite contrived. I don’t *think* this is going to really take away from any of the ideas. But I still want to highlight it because the idea of “data store” here isn’t going to look anything like SwiftData, CoreData, or other stuff a real app might use.

Also, this post builds on the topics discussed in the [last one](/step-by-step-network-request). Some of this stuff will be harder to follow if you don’t feel good about the content from there.

## Putting the pieces in place

Ok, so let’s start by defining the interface to our storage system.

```swift
class DataModel {
	let name: String

	init(name: String) {
		self.name = name
	}
}

class Store {
	func loadModel(named name: String) async -> DataModel {
		DataModel(name: name)
	}
}
```

I told you this was going to be contrived! There’s just a `DataModel` type to hold a simple value, along with a `Store` that “fetches” models for us. Neither do anything actually useful. But, it’s really just the types and their interfaces that we are concerned with.

Now we need a SwiftUI view to tie it all together.

```swift
struct ContentView: View {
	@State private var store = Store()
	@State private var name: String = "---"

	var body: some View {
		Text("hello \(name)!")
			.task {
				self.name = await store.loadModel(named: "friends").name
			}
	}
}
```

These two bits of code should fit very comfortably on one single screen. Not bad!

## Aside: Type system

I snuck in a little comment above that deserves more attention.

> But, it’s really just the types and their interfaces that we are concerned with.

This is important, and kind of subtle! Swift concurrency is an extension of the type system. I say this over and over because it’s important to understand. It means we can just play around with our types, their APIs and structure, and the compiler will give us feedback about their concurrent behaviors. You can often get considerable amounts of work done without even needing to run the code! That gives you a really fast feedback loop.

The ability to iterate on a design’s runtime behavior this way is cool.

## Great, except it doesn’t work

This example code is nice and small, but it actually does not compile in Swift 6 mode. The problem is that single line in the `task` modifier.

```swift
.task {
	// error: Non-sendable type 'DataModel' returned by implicitly asynchronous call to nonisolated function cannot cross actor boundary
	self.name = await store.loadModel(named: "friends").name
}
```

The error produced is … well let’s just say that it’s [non-ideal](https://github.com/swiftlang/swift/issues/77048). But that’s ok because we’re going to learn so much figuring it out!

Let’s break it down into three parts.

> Non-sendable type ‘DataModel’ …

Ok, so this is referring to our `DataModel` type from above. It looks like this:

```swift
class DataModel {
	// ...
}
```

It’s a class. Unlike structs, classes don’t conform to `Sendable` by default. And we haven’t added an explicit conformance. So, it makes sense the compiler is telling us that it is non-`Sendable`.

Next!

> … returned by implicitly asynchronous call to nonisolated function …

Oof. This is hard to decode. The clues we have here are “**returned by** blah blah **call to** blah blah **function**”. And we know what function is being invoked here. This is talking about our call to `Store.loadModel`. Let’s look at it more closely.

```swift
class Store {
	func loadModel(named name: String) async -> DataModel {
		DataModel(name: name)
	}
}
```

Right. This function is returning a `DataModel`, which we know does not conform to `Sendable`. But the compiler is telling us this call is “implicitly asynchronous” and that the function is “nonisolated”.

First, I’m terribly sorry to say that the word “implicitly” here is a compiler bug. It was [fixed](https://github.com/swiftlang/swift/issues/74472) quite a while ago, but that fix has not made it into a release yet. This is, ahem, an explicitly asynchronous call.

The critical bit is the compiler is telling us that the function is “nonisolated”. As we explored in the [previous post](/step-by-step-network-request), isolation comes from definitions. The `loadModel` function does not specify any isolation. And the `Store` type doesn’t either. No isolation is the default, and because we don’t see `@MainActor` or any other means of establishing isolation in these definition, that default applies.

Two down.

> … cannot cross actor boundary

Hmmmm. Actor boundary? We did’t use `actor` anywhere here, and we don’t (yet!) know what a boundary even means.

What we do know is `Store.loadModel` is both async and non-isolated. Non-isolated + async means runs in the background. So what this function is actually doing is creating a `DataModel` instance **in the background** and then passing it back to the caller.

But our caller is the SwiftUI view. That view is not in the background, it is on the `MainActor`. There is a “boundary” between these two things to prevent unsafe accesses. Here’s that line again:

```swift
self.name = await store.loadModel(named: "friends").name
```

Let’s re-write this compiler error:

> Hey! You are trying to leave the MainActor, go get a DataModel in the background, and then pass it back to the MainActor. But the only types I’m allowed to pass into or out of actors (like the MainActor here) are Sendable types. If the returned instance continues to be accessed in the background it would be a data race!

Oh.

## Just make it Sendable

Hopefully, this makes it clear *why* the compiler isn’t happy. And now it seems like there’s a really easy and obvious fix. Just make `DataModel` conform to `Sendable`!

```swift
final class DataModel: Sendable {
	// ...
}
```

Notice that to do this you also have to make the class `final`. `Sendable` classes cannot have subclasses. In this specific, contrived example, that was all it took. But, they also cannot have superclasses. They cannot contain mutable state. And any properties they do have must also be `Sendable`.

It turns out that when you want to make a class `Sendable`, it’s really only possible when that “class” is actually a struct. Structs, having value semantics, are much easier for the compiler (and humans…) to reason about. We *could* do that here, but only because our particular example is just incredibly simple. I’m going to leave it.

(There are some valid reasons for making `Sendable` classes, like sharing a single copy of a large immutable structure.)

Ok so we made this thing `Sendable` and we’re done right? Nope not done. Now there’s a **different** error.

```swift
.task {
	// error: Sending 'self.store' risks causing data races
	self.name = await store.loadModel(named: "friends").name
}
```

Oh FFS, what **now**?

## Sending self?

This is a subtle issue. The clues we have to go on are word “Sending” and the reference to `self.store`.

We can see that `self.store` is an instance variable of our view. And because it is a member of a `MainActor` type (via that SwiftUI `View` conformance), it is also `MainActor`-isolated.

```swift
// This is @MainActor ...
struct ContentView: View {
	// ... so this is too
	@State private var store = Store()

	// ...
}
```

Now here’s where the subtly comes in. I’m going to add just a little bit of code and put these two things side by side to show what’s going on.

```swift
// the "store" here...
self.name = await store.loadModel(named: "friends").name
```

```swift
func loadModel(named name: String) async -> DataModel {
	print(self) // ... needs to end up as "self" here!

	return DataModel(name: name)
}
```

Ok, so think about what’s happening. We have the `store` instance, which is isolated to the `MainActor`. To make this call to `loadModel`, we have to get to the background. And, because this is an instance method, that `store` variable needs to become `self` inside the method body.

The receiver of a method call is an implicit parameter!

So, the instance needs be “sent” from the `MainActor` into the background, which is an actor boundary. Does this sound familiar?

Only `Sendable` types can do that!

## Aside: MainActor means Sendable

Here’s something interesting that’s really important to know. You get an implicit `Sendable` conformance when you mark a type with `MainActor`.

When I first learned this, it **really** surprised me!

Types that are isolated to a global actor give the compiler enough information to guarantee safe access no matter where it occurs. And that’s enough to satisfy the requirements of `Sendable`.

Here’s something I sometimes run into.

```swift
@MainActor // This makes the type Sendable
class SomeClass: Sendable {
}
```

The redundant `Sendable` isn’t **wrong**, but it should cause you to raise an eyebrow. Probably just left-over from experiments along the way, but something I usually call out.

You can go [deeper](/non-sendable) here if you want. Or you can just remember that `@MainActor` means `Sendable`. Ok.

## Non-Sendable + async you say?

(Here’s the code again, just for reference.)

```swift
class Store {
	func loadModel(named name: String) async -> DataModel {
		DataModel(name: name)
	}
}
```

When we talk about “boundaries” in this case we’re talking about the transitions between the `MainActor` and the background. There’s one making the call, and then there’s a second when we return. The compiler requires that all the stuff that crosses boundaries be `Sendable`. This is why non-`Sendable` types that have async methods, or participate in concurrency at all, should always raise alarm bells. They are very hard to use!

Hard does not mean [impossible](/non-sendable), though. And in fact they can be quite powerful. But they are very advanced, and it is **extremely** common for people to introduce them into their code without realizing the implications.

There is a very strong correlation between people having trouble with Swift concurrency and falling into this trap.

(Not that I blame them. The language should not have traps like this! It won’t come for free, but thankfully the Swift team is [working](https://forums.swift.org/t/pitch-inherit-isolation-by-default-for-async-functions/74862) on changing the semantics of the language to address this.)

## Thinking is now, unfortunately, required

As soon as you have to cross one of these boundaries, by moving values into or out of an actor, it requires some thought. **All** the types that are involved now have to become `Sendable`. That constraint can range from no big deal to complete showstopper.

Astute readers of the first post will note that I exploited this to keep the content simpler. There were boundary crossings all over the place, but all the types were `Sendable` and everything just worked. This wasn’t (entirely) contrived either - it actually does happen in practice. The app we made did a real, if ridiculous, thing! How often that actually happens is largely a function of how much immutable data you are working with.

Now speaking of thinking, let’s now figure out what to do here.

## Just remove the boundaries

If you cannot make the values `Sendable`, the simplest solution here is to just stop crossing boundaries in the first place. But how?

Well, we know that we’re going from `MainActor` -> background on call, and then we’re going background -> `MainActor` on return. Let’s just stop going to the background.

```swift
@MainActor // <- apply isolation!
class Store {
	func loadModel(named name: String) async -> DataModel {
		DataModel(name: name)
	}
}
```

By isolating `Store`, all our problems go away. It no longer **matters** that `DataModel` isn’t `Sendable`, because it doesn’t have any boundaries to cross. Our `Store` type also now becomes `Sendable`, so it makes it much easier to use with other concurrency constructs.

Of course, this comes with a pretty big trade-off. We’re now forced to do any work involving the creation of this `DataModel` instance on the main thread. And that could be a problem.

## “Split isolation”

Before we get into all that, there’s an alternative, similar solution I want to highlight.

```swift
class Store {
	@MainActor // <- apply isolation to just the method
	func loadModel(named name: String) async -> DataModel {
		DataModel(name: name)
	}
}
```

Instead of isolating the entire type, we just apply it only to the async function. This works! However, this pattern is incredibly problematic. I encounter this so often, and it causes so many problems that I gave it a name: “split isolation”.

To understand why this is a problem, think about just this method. We know that `self` needs to move from the call site into `loadModel`. But, note that `Store` is **not** `Sendable`. This means that in order to call this method on an instance, the instance has to **already be** on the `MainActor`! And because it isn’t `Sendable`, participating in concurrency in any methods with different isolation are going to be really hard/impossible.

You’ve got this one single instance, but only some parts can be used when off the `MainActor`. It has been “split” between `MainActor` and non-isolated. I dunno, if you come up with a better name let me know.

Again, there **are** valid uses for this pattern. But, if you cannot articulate exactly **why** you are doing it and how you’ll deal with the implications, you shouldn’t be doing it. If you are going to use `@MainActor`, apply it to the whole type.

Just had to get that out of the way. Onward.

## Value types

Ok ok, but what if you just want to do some work in the background? Forget possible, shouldn’t that be **easy**?

We saw above that making a class `Sendable` is nearly equivalent to making it a struct. Working with value types gives us a lot of options. Let’s do that now.

```swift
struct DataModel {
	let name: String

	init(name: String) {
		self.name = name
	}
}

@MainActor
class Store {
	func loadModel(named name: String) async -> DataModel {
		let data = await Self.readModelDataFromDisk(named: name)
		let model = await Self.decodeModel(data)
		
		return model
	}
	
	private nonisolated func readModelDataFromDisk(named name: String) async -> Data {
		// hit the disk in the background
	}
	
	private nonisolated func decodeModel(_ data: Data) async -> DataModel {
		// process the raw data in the background
	}
}
```

When it comes to offloading work to other threads, the details will always matter. But here, I’ve just made up two plausible processing steps.

Both are non-isolated async functions, and that means they run in the background. Because they are non-isolated, they cannot access the`MainActor` members of `Store` synchronously, but that could be fine! These could be just plain old, stateless functions. They take immutable input and produce immutable output.

This often works out really well. It can be an excellent solution to a classic load-and-decode like this. It’s an extremely common pattern - it came up in the previous post too. I think this should **always** be what you reach for first.

Unfortunately, real systems may not be so easy to get into this pure `Sendable`-in, `Sendable`-out shape. And that’s when you have to start looking at alternatives.

## Swift 5 module

A setup that you might like is a companion Swift 5 module **without** warnings enabled. It’s just a nice place to stash stuff that you can’t or don’t want to get working in 6 mode. It’s also a great option when interfacing with existing systems. Modularity is one of the keys to a successful Swift 6 migration.

```swift
class Store {
	func loadModel(named name: String, completionHandler: @escaping @MainActor (DataModel) -> Void) {
		someQueue.async {
			// expensive work goes here
			let model = DataModel(name: name)
			
			DispatchQueue.main.async {
				completionHandler(model)
			}
		}
	}
}
```

The whole reason for doing this is to get a non-`Sendable` type from the background to the main thread. I’ve annotated the API with `@MainActor` so it will look to callers like there’s no boundary at all. Done.

Perhaps surprisingly, this code actually compiles **without error** in Swift 6 mode. There is a lot going on internally to make this possible. But, what you really need to know is the compiler understands that `model` can safely move from the background to main **in this specific case**. It can only determine this because a) this is all happening within one function and b) this example is simple. But it’s still pretty interesting to know that stuff like this is possible.

(The system that does this analysis is called “region-based isolation”, and I’ve [written](/concurrency-swift-6-se-0414) about it.)

My own preference is to make a clear distinction between APIs that are **using** concurrency and those built to work around a problem. I don’t think you should write `async`/`await` in modules that have concurrency warnings disabled. If you want to make an async wrapper around this function, you should do that in an extension within a module that has the warnings on.

## The `sending` keyword

Way back, I re-wrote the compiler error message, and ended with this:

> If the returned instance continues to be accessed in the background it would be a data race!

Note the **if**. This is true, but we **don’t** actually continue to access it. This warning we are trying to work around is actually a false-positive.

The thing is, it is a false-positive **right now**. But that’s really a function of our implementation. We could make tiny changes that could render this unsafe very easily.

Swift 6 recognizes how much of a pain this can be though, and introduced a new feature to help. The `sending` keyword allows us to encode this promise of safety into our API. We can use it to express this idea that we are producing a new, independent value and just passing over to the caller. Here’s the idea.

```swift
@MainActor
final class Store {
	nonisolated func loadModel(named name: String) async -> sending DataModel {
		DataModel(name: name)
	}
}
```

We’ve done two things. First, we’ve removed the `MainActor`-ness with the `nonisolated` keyword, which gets us onto the background. The type is still `Sendable`, because it remains `MainActor`-isolated.

But the interesting bit is that `sending` keyword applied to the return value. What `sending` does is make a trade. It accepts a constraint with the function body, but in exchange, it relaxes constraints at call sites.

We’re guaranteeing that our API will always provide an instance of `DataModel` that can safely be returned. It’s kinda like `Sendable`, but instead of applying to the whole type, its just this one spot. To make that work, the compiler needs to prove `loadModel` actually provides that guarantee.

`sending` isn’t magic. There are situations where it just won’t work, even when it seems like it should. And I have found those difficult to debug. But regardless, it is a very powerful tool!

## Actors

So far, we’ve only ever talked about `MainActor`, or “the background”. But you can make your own actors too! This gives you a way to define a new little corner of isolation.

```swift
actor Store {
	func loadModel(named name: String) async -> sending DataModel {
		DataModel(name: name)
	}
}
```

We do still need the `sending` here, because `DataModel` still has to move from this actor’s isolation to the outside world. But this does look simpler. We also no longer need a non-isolated method to get off the main thread. And, because the method is isolated, all this actor’s properties are synchronously accesible within its body. So far, this seems great!

Well, the thing is actors come with 2.5 problems.

The first is their interface is **strictly** asynchronous. A `MainActor` version of `Store` could be accessed synchronously if needed, but this actor version cannot. This can be a killer, especially for an existing system. You should always be paying **extremely** close attention to where you need synchronous access to data when working with Swift concurrency.

The second is the isolation that an actor provides is a double-edged sword. Every single input and output to an actor now needs to cross a boundary. This can be a huge problem. In general, when you add an actor to a system, you are **increasing** the need for yet more `Sendable` types. More actors means more boundaries.

The last half-a-problem is that actors are more likely to encounter reentrancy issues. The reason I count this as a half is reentrancy can be an problem even with a purely `MainActor` system. In fact, it isn’t even unique to Swift concurrency - this problem can and does happen with GCD too.

Reentrancy is too big a topic to cover here as well, but I want to at least put it into your head. Actors are not the first thing you should look to. In fact, I think they are extremely over-used!

## The end…

Would you believe that I actually removed a bunch of content from this before posting? I originally had some stuff in here about using the various unsafe opt out tools the language provides. But, re-reading, I decided that’s just something for another day. Things like `@unchecked Sendable` and `nonisolated(unsafe)` exist for a reason, and let you do basically anything you want. But they have more [downsides](https://jaredsinclair.com/2024/11/12/beware-unchecked.html) than you might think!

I also **really** hesitated to introduce `sending` and actors in this post. But, ultimately I decided it made sense, because they are real, useful tools. But they should **both** should give you pause. They encourage yet more concurrency. More concurrency means more complexity. And I am, firmly, of the opinion that you should introduce complexity like this only when the trade-off can be **justified**.

If you can pull off what you need using some value types and a few non-isolated functions here and there, you should. It’s just so much simpler. Unfortunately, you will encounter situations where these won’t cut it. That’s what the other options are for.

And now there’s a [third installment](/step-by-step-stateful-systems) if you’ve been enjoying these!

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
