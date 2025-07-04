```markdown
# ModelActor is Just Weird

Mar 22, 2025

I actually don’t get too many questions about SwiftData or Core Data. And thank goodness, because I’m not particularly familiar with either. That is, until just recently! I had the chance to work with two different projects, both of which were using SwiftData. While Core Data was introduced in 2005, this SwiftData stuff is brand new. In fact, it includes a whole bunch of Concurrency-specific features. It should be smooth sailing right?

Well, spoiler, it’s not. It’s close! But it’s also very strange. This post is all about understanding why it is strange, dealing with it, and learning a bunch about concurrency along the way.

But first! I want to take a moment to say thank you. Both of these clients I worked with agreed to let me share the experiences and code. One even specifically asked me to blog about it! This was incredibly cool.

**Update**: multiple people have since reached out to tell me about yet more `ModelActor` behavior related to its interaction with the main thread. This post does not fully explain what’s going on or how to deal with it.

## ModelActor

My understanding is that SwiftData is a fairly thin wrapper around Core Data. Now, when someone takes the time to outline [laws](https://davedelong.com/blog/2018/05/09/the-laws-of-core-data/) around a framework, you should probably tread carefully. So, no doubt there’s lots of historical stuff going on here.

But, that still doesn’t explain how much [trouble](https://brightdigit.com/tutorials/swiftdata-modelactor/) people have with [ModelActor](https://developer.apple.com/documentation/swiftdata/modelactor). I’m not sure **anyone** has ever used `ModelActor` without at least some surprises.

Let’s look more closely at it.

`ModelActor` is a protocol, but you are supposed to interact with it using the `@ModelActor` macro. The purpose of this combo is to provide “mutually-exclusive access to the attributes of a conforming model”.

```swift
@ModelActor
actor MyModelActor {
}
```

Expanding the macro, we can see that this resolves to the following:

```swift
@ModelActor
actor MyModelActor {
	nonisolated let modelExecutor: any SwiftData.ModelExecutor

	nonisolated let modelContainer: SwiftData.ModelContainer

	init(modelContainer: SwiftData.ModelContainer) {
		let modelContext = ModelContext(modelContainer)
		self.modelExecutor = DefaultSerialModelExecutor(modelContext: modelContext)
		self.modelContainer = modelContainer
	}
}

extension MyModelActor: SwiftData.ModelActor {
}
```

This gives us the full picture of a minimal “ModelActor” type. Hanging onto the `modelContainer` seems reasonable. And making a new `ModelContext` makes sense. But, there’s definitely some funny business happening with this `modelExecutor`.

It appears that the SwiftData machinery here needs to use a custom actor executor. This is typically so you can have more control over how an actor executes code. This is **probably** required for compatibility with Core Data’s [concurrency model](https://developer.apple.com/documentation/coredata/using-core-data-in-the-background). But it’s hard to be sure because as far as I can tell, this is not documented.

## The Problem

Putting the internals aside, the truly important thing about `ModelActor` is protecting that [`ModelContext`](https://developer.apple.com/documentation/swiftdata/modelcontext) property. This type is non-Sendable. Which means it is not thread-safe and requires some form of synchronization.

Actors exist to protect mutable state. The purpose of a `ModelActor` is to own and isolate the `ModelContext`. It does that! But if we start to dig into **how** exactly it does it, we will discover something very bizarre.

Here’s an example that illustrates the issue with a minimal SwiftUI program.

```swift
// let's define a model
@Model
final class Item {
	var name: String
	
	init(name: String) {
		self.name = name
	}
}

// put together a quick-and-dirty global container
extension ModelContainer {
	static var shared: ModelContainer {
		try! ModelContainer(
			for: Schema([Item.self]),
			configurations: .init(isStoredInMemoryOnly: true)
		)
	}
}

// Here's our star, the ModelActor type
@ModelActor
actor MyModelActor {
	func hello() {
		print("hi!")
	}
}

// and now create a view that uses the actor
struct ContentView: View {
	@State private var database = MyModelActor(modelContainer: .shared)
	
	var body: some View {
		Text("Hello ModelActor!")
			.task {
				await database.hello()
			}
	}
}
```

If you run this code, you’ll see “hi!” in the console. So far so good. But now, let’s make a teeny-tiny little modification.

```swift
@ModelActor
actor MyModelActor {
	func hello() {
		MainActor.preconditionIsolated() // WAT
		print("hi!")
	}
}
```

This precondition will **hold**. Somehow, we are on our custom, minimal, SwiftData-defined actor **and** also the `MainActor` at the same time.

This is.. well… I don’t know what this is, but it is not normal.

## Is this thing an actor or what?

Just to prove to you that this is strange, if we substitute in a source-compatible actor that doesn’t use this macro, we’ll crash.

```swift
actor MyModelActor {
	init(modelContainer: ModelContainer) {
	}

	func hello() {
		MainActor.preconditionIsolated() // NOPE
		print("hi!")
	}
}
```

Stock actors do not run code on the main thread. You totally *could* make an actor that does. But **why** would you? Doing it is the **worst** of all possible options.

It is bad because consumers of this API have a very reasonable expectation that this will execute off the main thread. This type doesn’t do that. But worse, its relationship with the main thread isn’t visible in the type system. These things are **not** marked `MainActor`, so the compiler doesn’t know what’s going on. This means even though you are on the main thread here, you cannot access `MainActor` stuff.

But, don’t get mixed up. It is still “an actor”. It still is able to protect mutable state. It is perfectly legitimate to protect your state by using the main thread. That’s how `MainActor` does it, after all.

This is just, in my opinion, a really bad way to do it. `@ModelActor` makes a type that ties up the main thread but doesn’t give you the ability to access main thread state. It’s a lose-lose.

## Context matters

As many others have discovered, a `ModelActor` type is sensitive to where it is created. If you make one on the main thread, you’ll get an actor that uses the main thread for isolation. But if you init the exact same type in the background, you get (as far as I can tell) regular old actor execution behavior.

But just how exactly are we supposed to do that?

All we need is a non-main execution context. I think! Honestly, this isn’t documented so I actually don’t know what is going on internally. But I suspect that this mirrors Core Data’s concurrency model, which makes a distinction between main and private queues. So, this all seems like a good guess and appears to work in practice.

```swift
@MainActor
func makeMainModelActor() -> MyModelActor {
	MyModelActor(modelContainer: .shared)
}

func makeBackgroundModelActor() async -> MyModelActor {
	MyModelActor(modelContainer: .shared)
}
```

What I’m doing here is using a non-isolated async function to guarantee I’m not on the main thread. That seems to be all it takes.

(If you are surprised that non-isolated + async = background, check [this](https://www.massicotte.org/step-by-step-network-request) out.)

## Background access

Once you understand that `ModelActor` types are sensitive to where they are created, there are many ways to deal with it. But many projects actually need two interfaces to their database. One that provides synchronous access from the `MainActor`, and another that allows background operations and doesn’t block the main thread.

While the MainActor version isn’t usually problematic, the background one is. All of our work needs to involve the `ModelContext`. But that type isn’t `Sendable`. Which means it is “trapped” inside of our `ModelActor`. How do we get at it?

Instead of trying to get the non-`Sendable` stuff **out**, we are going to push the work we need to do **in**. We’re going to build this up slowly, because we need quite a complex system to be fully general.

First, we’ll start with an extension on `ModelActor`.

```swift
extension ModelActor {
	func withContext<T>(
		_ block: (ModelContext) -> T
	) -> T {
		block(modelContext)
	}
}
```

This signature gives us a way to submit work to our `ModelActor` that needs to touch its `modelContext` property. It’s safe to access `modelContext` here because this block is being executed in a function that is isolated to the `ModelActor` instance. We’ve moved the work into the actor. We even added a generic so this work can produce an arbitrary result.

However, this isn’t going to work very well yet. We’re missing a core ingredient. See the whole idea is to move the closure from over here (gestures left) into this actor (gestures right). We want to “send” it into the actor. Would anyone like to guess what that means?

This closure has to be `@Sendable`!

```swift
extension ModelActor {
	func withContext<T>(
		_ block: @Sendable (ModelContext) -> T
	) -> T {
		block(modelContext)
	}
}
```

A `@Sendable` closure is free to move from one isolation domain to another. It can cross the boundaries between them. In fact, it’s even more powerful than that. A `@Sendable` closure is fully thread-safe. It could be executed from multiple threads **simultaneously**.

In this case, we don’t actually need something with so many guarantees.

We just want to tell the compiler that we need to move this closure into the actor, right at the callsite. And there is a way to express this - with the `sending` keyword. This is much lower bar, and it’s exactly we need. Doing this makes our API much easier to use, because there are more constraints on a `@Sendable` closure.

With this, we now have a minimally-usable version.

```swift
extension ModelActor {
	func withContext<T>(
		_ block: sending (ModelContext) -> T
	) -> T {
		block(modelContext)
	}
}
```

(I was a little surprised that this code fails at `MainActor` callsites without an explicit `sending` or `@Sendable`. I thought that [Region-based isolation](https://www.massicotte.org/concurrency-swift-6-se-0414) would make this “just work” in many cases. Anyways, this code is clear and I like it, but if you know what’s up please tell me.)

## sending sending sending

Progress, but there are still some serious limitations. The first is that you’ll find actually returning values are only possible when T is `Sendable`. This makes sense though! The work is happening in the actor and to get values out, we need to “send” them from the actor back to the caller. Inputs have to be sent in, outputs have to be sent back out.

We can express this as a generic constraint.

```swift
extension ModelActor {
	func withContext<T: Sendable>(
		_ block: sending (ModelContext) -> T
	) -> T {
		block(modelContext)
	}
}
```

The thing is, it’s kind of redundant because the compiler is going to enforce this regardless. And we don’t need fully `Sendable` types anyways. We just need to promise that we will only return stuff that is safe to send. That’s what `sending` does, so let’s use it again.

```swift
extension ModelActor {
	func withContext<T: Sendable>(
		_ block: sending (ModelContext) -> T
	) -> sending T {
		block(modelContext)
	}
}
```

Ok, great! Now we can get rid of the generic constraint and allow more flexible return value types! This will make our API much easier for callers to use.

Except that does not compile…

```swift
extension ModelActor {
	func withContext<T>(
		_ block: sending (ModelContext) -> T
	) -> sending T {
		// Returning 'self'-isolated 'self.modelContext' as a 'sending' result risks causing data races
		block(modelContext)
	}
}
```

What the compiler is trying to tell us here is basically “I don’t know what this `block` is going to return, what if it grabs a reference to `modelContext` and returns that!”.

This is an interesting little peek into the kind of reasoning the compiler has to do to prove that something can be “sent”. And it’s right. Consider this in code form:

```swift
let unsafeContext = await modelActor.withContext { $0 }
```

Without this check, we’d be allowed to smuggle the thread-unsafe `ModelContext` instance out of actor and access it from other threads! But, how do we address this? What we need is a block that only returns things that are safe for us to then return as `sending`. Did you guess a third `sending`?

```swift
extension ModelActor {
	func withContext<T>(
		_ block: sending (ModelContext) -> sending T
	) -> sending T {
		block(modelContext)
	}
}
```

It’s just a sending value returned from a sending closure that is then sent. Easy!

Jokes aside, I think it actually is very educational to sit and think about this. The inputs to this actor method have to move from “the outside” into this actor (sending closure), and then the outputs have to be moved back to “the outside” (sending return). The closure needing to have a sending return might feel funny though. We’re promising to return a sending value, but we’re just returning whatever that block is returning. This means the block needs to keep the same promise.

### Errors

Ok, we are actually getting somewhere now. This is now quite usable. However, it would be a lot more convenient if our block could throw. That’s not too hard to wire up, actually.

```swift
extension ModelActor {
	func withContext<T>(
		_ block: sending (ModelContext) throws -> sending T
	) rethrows -> sending T {
		block(modelContext)
	}
}
```

We can allow the block to throw, and then mark the method `rethrows`. This definitely works, but we could also try using that fancy new typed throws stuff.

```swift
extension ModelActor {
	func withContext<T, Failure: Error>(
		_ block: sending (ModelContext) throws(Failure) -> sending T
	) throws(Failure) -> sending T {
		try block(modelContext)
	}
}
```

We need another generic, and the signature is starting to get pretty dense. But this is a more generalized system so I’m going to leave it.

## Making it async

What we have at this point isn’t too bad. We don’t require `Sendable` types and we have typed errors. But there’s one more limitation. That block of ours currently only permits synchronous code. We can address this, but it’s going to be the biggest challenge yet.

First the straightforward stuff:

*   make the block `async`
*   make the method `async`
*   call the block using `await`

```swift
extension ModelActor {
	func withContext<T, Failure: Error>(
		_ block: sending (ModelContext) async throws(Failure) -> sending T
	) async throws(Failure) -> sending T {
		try await block(modelContext)
	}
}
```

These three changes aren’t too bad. But, they result in a compiler error at the block callsite:

```plaintext
Sending 'self.modelContext' risks causing data races
```

I wouldn’t be surprised if at this point you got stuck. We **can** resolve this, but it’s very tricky. First, let’s understand the problem.

The compiler is telling us that we are somehow using `modelContext` in an unsafe way. Remember the whole reason for doing all of this garbage is to run this block within the isolation of the actor.

Check out the type of the block:

```swift
(ModelContext) async throws(Failure) -> sending T
```

It is an async function. But, critically, it also doesn’t have any isolation defined. What do we know about non-isolated + async? Background thread.

This call would move `modelContext` from the protection of this actor out to an arbitrary background thread. That is crossing an isolation boundary. Because `ModelContext` is not Sendable, that is not allowed.

Here’s much simpler example with the same issue:

```swift
(NonSendable) async -> Void
```

Functions that have this form will almost always be problematic.

## Isolated parameters

To make this contraption of ours work, we somehow need this call to `block` without changing isolation. We need it to execute on the actor instance.

There are four ways to define static isolation.

*   None, which is `nonisolated`
*   Actor methods, which are isolated to the actor instance
*   Global actor annotations, like `@MainActor`
*   isolated parameters

This block is actually using the default. With nothing else present, you get `nonisolated`. We cannot use an actor method, because the whole point is to have this work defined **outside** of the actor.

A global actor annotation also won’t help us. Because all we’d be doing is moving `modelContext` from the current actor out to that global actor. That’s just crossing a different isolation boundary. We need no boundary at all.

An isolated parameter is exactly the right tool. It gives us a way to say “run this async method isolated to **whatever I pass in**”.

```swift
extension ModelActor {
	func withContext<T, Failure: Error>(
		_ block: sending (isolated Self, ModelContext) async throws(Failure) -> sending T
	) async throws(Failure) -> sending T {
		try await block(self, modelContext)
	}
}
```

Here we’ve made two changes. First, we have changed the block to accept an isolated parameter. And second, we have passed in `self`, the instance of this actor, to the block. Remember we are extending a protocol here, so to refer to a conforming type, we use `Self`.

The translates to: “Run this async function isolated to me”.

(Also, just in case this whole isolated parameter dance is getting you down, the compiler team is working on [improving](https://forums.swift.org/t/se-0461-run-nonisolated-async-functions-on-the-callers-actor-by-default/77987) this situation and I’m very excited for it.)

## A bug?

Honestly, at this point, I thought we were done. But it turns out that with Swift 6.1 (Xcode 16.3b3), this implementation is problematic. I’m unable to get the compiler to accept a version of this code that uses a `sending` block and an isolated parameter. Whenever I try, I get errors at the points of use. We’re getting into pretty complex territory here, but I **think** this code should compile.

Anyways, the only solution I could come up with was to make the closure `@Sendable`, so that’s the final version here:

```swift
extension ModelActor {
	func withContext<T, Failure: Error>(
		_ block: @Sendable (isolated Self, ModelContext) async throws(Failure) -> sending T
	) async throws(Failure) -> sending T {
		try await block(self, modelContext)
	}
}
```

This isn’t **that** bad, so I’m ok with it.

## A more complete system

What we have now is a general purpose extension on all `ModelActor` types that can accept and execute work within that actor. But if you can remember that far back, we were just trying to get a handle on `ModelActor`’s weird context-sensitive initialization.

We want a system that makes it easier to access our SwiftData system on the MainActor or background, as needed.

I’ve punished you enough with these step-by-step code transformations. So, I’ll just present the final solution here and then we can discuss a bit.

```swift
@MainActor
struct Database {
	@ModelActor
	actor Background {
		static nonisolated func create(container: ModelContainer) async -> Background {
			Background(modelContainer: container)
		}
	}
	
	public let mainContext: ModelContext
	private let task: Task<Background, Never>
	
	init(container: ModelContainer) {
		self.mainContext = container.mainContext
		self.task = Task { await Background.create(container: container) }
	}
	
	public var background: Background {
		get async { await task.value }
	}
}
```

There are three important things to note about this `Database` type.

*   The first is that it is `MainActor`. This makes it easy to incorporate into a SwiftUI application. This is also important for convenient access to the main-thread-only `mainContext` property.
*   The second thing is the nested `Background` actor. This is a `ModelActor` type with exactly one factory method. But, because that method is non-isolated and async, it will always run on the background. This let’s us create the `Background` actor in a non-main context so it actually runs in the background.
*   The last thing is because this `create` method is async, we need a `Task` somewhere. I’ve opted to internalize this and hang onto the `Task`. This let’s us asynchronously access the `Background` actor when needed. I admit this is awkward, but I think it is highly desirable to keep the `init` method of `Database` synchronous.

## Usage

I actually haven’t spent much time actually using these ideas. But we can at least take a peek at what that could look like.

```swift
let database = Database(container: .someContainer)

let result = try database.mainContext.fetch(someDescriptor)

let asyncResult = try await database.background.withContext { _, context in
	try context.fetch(someDescriptor).property
}
```

I kind of don’t even know what I’m doing here. But I think you get the idea of the programming model. I believe this stuff can be used as a building block for a much more full-featured system around SwiftData. Or you can just use it directly if your needs are simple.

It is worth noting, though, that I’ve just ignored that isolated parameter field. This is fairly common with isolated parameters actually! You often can just ignore it during regular use of the API.

Another point is we have only one single `Background` actor here. It will serialize access to its `modelContext`, which means it can only do one operation at time. This can be a major drawback if you need to execute multiple long-running queries. But, I believe we could push this general idea further if multiple concurrent operations were necessary.

## But ugh

It was fun and quite educational to figure this all out. But, it’s also pretty annoying. This was a lot of work to solve problems that, in my opinion, shouldn’t even exist. That extension on `ModelActor` should probably be built into the framework. And this contextually-sensitive `ModelActor` stuff makes no sense to me. At the absolute least, this needs to be carefully documented so developers understand how to use the type correctly.

Something fascinating is that I **think** SwiftData could change `ModelActor` and most things would still work. All accesses already need `await`. `MainActor` stuff would remain off-limits. In fact, the only problem I can think of is if someone is inadvertently depending on the main thread nature of `ModelActor` and **also** has concurrency warnings off. Aside from that unfortunate situation, the fact that such a major change could be made while preserving source compatibility is kind of amazing.

In the meantime, I hope this is all useful. Remember, I have very little SwiftData experience! So, there could be a better option lurking out there that’s nicer. If you know of one, please share.
```
