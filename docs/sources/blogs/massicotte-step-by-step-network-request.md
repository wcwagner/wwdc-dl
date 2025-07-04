# Concurrency Step-by-Step: A Network Request

Aug 14, 2024

When I was first learning to program I had **absolutely** no idea what I was doing. I was using C, and I remember desperately putting in \* and & characters until things compiled. But, this was pre-Mac OS X. Upon running my horrifically incorrect programs, half the time the screen would become corrupted and the mouse would stop moving. I’d then have to reboot the whole machine via a physical switch. This was … frustrating.

Mercifully, the development experience has improved significantly. But, even today, when you don’t understand warnings/errors, I think it’s very understandable to do the same thing. However, just throwing syntax at the problem is not how you build a solid foundation. I want your experience to be better than mine, particularly when learning Swift concurrency. It’s important, because yeah I want your code to compile. But, I also want you to avoid the structural problems that can come along with making changes you might regret later.

It was a mistake that I haven’t paid more attention to people just getting started. I’m going to try to fix that by getting into some basics. Let’s go step-by-step though a network request with SwiftUI.

## Preface

A few quick notes. First, I’ve pretty much omitted all error handling. I did this to keep focus on the topic at hand. I also am not a particularly sophisticated SwiftUI developer, so this might have some bad patterns.

Critically, this post was written for **Xcode 16**. If you are using an earlier version, some things will not work the same.

## Putting the pieces in place

Let’s take a look at a very simple SwiftUI program that loads something from the network. I needed to find a free API to use, and settled on [Robohash](https://robohash.org). It is a delightful mix of simple, interesting, and quirky.

Since our data is going to be loaded from the network, we have to handle the case where we have nothing to display. We’ll start with a little view that can handle an optional image.

```swift
struct LoadedImageView: View {
	let cgImage: CGImage?
	
	var body: some View {
		if let cgImage {
			Image(cgImage, scale: 1.0, label: Text("Robot"))
		} else {
			Text("no robot yet")
		}
	}
}
```

I used `CGImage` here so this code can work unmodified on all Apple platforms.

Now, we can get into the more interesting stuff. Let’s make a view that actually loads some data from the network.

```swift
struct RobotView: View {
	@State private var cgImage: CGImage?

	var body: some View {
		LoadedImageView(cgImage: cgImage)
			.onAppear {
				loadImageWithGCD()
			}
	}
	
	private func loadImageWithGCD() {
		let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)

		let dataTask = URLSession.shared.dataTask(with: request) { data, _, _ in
			guard let data else { return }

			DispatchQueue.main.async {
				let provider = CGDataProvider(data: data as CFData)!

				self.cgImage = CGImage(
					pngDataProviderSource: provider,
					decode: nil,
					shouldInterpolate: false,
					intent: .defaultIntent
				)
			}
		}

		dataTask.resume()
	}
}
```

I’ve used GCD. Hopefully this keeps things looking familiar if you haven’t gotten into concurrency at all. But, I do still want to note that I’m using the Swift 6 language mode here and this code compiles error-free.

Here’s what’s happening:

*   when the view becomes visible, we invoke `loadImageWithGCD`
*   a `URLRequest` is created
*   a `URLSessionDataTask` is configured to make the request
*   the response is eventually returned **on a background thread**
*   we shift back to the main thread to process the data and update our state

(If you’d like to go on a side quest, there’s a [great post](https://oleb.net/2024/dispatchqueue-mainactor/) that explains how the compiler is able to determine that this GCD-based code is safe.)

## I/O vs CPU

There are two key phases to this operation. The request and the processing. The request is **I/O-bound**. Once issued, we don’t have to be involved at all until the response is available. This means our UI is responsive and the app could do more work.

The second phase is **CPU-bound**. Converting the PNG data into a `CGImage` is synchronous work that ties up the thread until it is done. We’re doing this all on the main thread using that `DispatchQueue.main.async`. Our UI is **not** responsive during this second phase.

I like to think of being I/O-bound as **waiting**. We can do other stuff while we’re waiting. On the other hand, I think of being CPU-bound as **working**. We cannot do other stuff, because we’re busy.

Let’s see if we can restructure things so the app will be more responsive during all this.

## The wrong way

As it turns out, converting the data into a `CGImage` is pretty darn fast. At least it is on machine, with its OS, and with the data I’m requesting right now. But all those variables could potentially impact the performance. Ok fine, this might be a little contrived, but we still don’t want to get in the habit of blocking the main thread.

Remember the callback from `dataTask` executes on a **background thread**? Let’s just do everything there!

```swift
private func loadImageWithGCD() {
	let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)

	let dataTask = URLSession.shared.dataTask(with: request) { data, _, _ in
		guard let data else { return }

		let provider = CGDataProvider(data: data as CFData)!

		// ERROR: Main actor-isolated property 'cgImage' can not be mutated from a Sendable closure
		self.cgImage = CGImage(
			pngDataProviderSource: provider,
			decode: nil,
			shouldInterpolate: false,
			intent: .defaultIntent
		)
	}

	dataTask.resume()
}
```

We have a problem though. The `self.cgImage` property is a component of our UI, and is only safe to work with on the main thread. The compiler won’t let us get way with this.

> Main actor-isolated property ‘cgImage’ can not be mutated from a Sendable closure

What it is actually telling us, though, is a little hard to understand. The “Sendable closure” here is the closure we are providing to `dataTask(with:completionHandler:)`. Let’s look at its definition.

```swift
func dataTask(
    with request: URLRequest,
    completionHandler: @escaping @Sendable (Data?, URLResponse?, (any Error)?) -> Void
) -> URLSessionDataTask
```

In order to find out what thread `completionHandler` runs on, we would have to hunt through documentation. But, Swift concurrency has moved this information into the type system. And you can see it right there: `completionHandler` is `@Sendable`. This means, more or less, “I may run this closure on a background thread”.

Let’s try again.

## The right way

We have to be more careful about where we do our UI-related work. To do that, we’ll bring back the `main.async`.

```swift
private func loadImageWithGCD() {
	let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)

	let dataTask = URLSession.shared.dataTask(with: request) { data, _, _ in
		guard let data else { return }

		let provider = CGDataProvider(data: data as CFData)!

		let image = CGImage(
			pngDataProviderSource: provider,
			decode: nil,
			shouldInterpolate: false,
			intent: .defaultIntent
		)

		// Must make sure we do this on the main thread
		DispatchQueue.main.async {
			self.cgImage = image
		}
	}

	dataTask.resume()
}
```

Now we have a safe version, and it follows a very common pattern. The bulk of the work is done in the closure body, which we know is in the background. And we then produce a final result `image` that is passed along back to the main thread to update our UI.

Ok, now let’s try to do this with `async`/`await`.

## Async

Before we get started we need a tiny bit of infrastructure in place. In order to run async code, we need an **async context**. You cannot make async calls from regular, synchronous functions.

SwiftUI gives us the `task` modifier to do exactly this.

```swift
struct RobotView: View {
	@State private var cgImage: CGImage?
	
	var body: some View {
		LoadedImageView(cgImage: cgImage)
			.task {
				// you are allowed to use await in here
				await loadImageAsync()
			}
	}
}
```

This is really similar to the `onAppear` modifier we were using before. Both are kicked off as soon as the view becomes visible. But, this version gives us the async context we need to call async functions.

Now, let’s write `loadImageAsync`.

```swift
private func loadImageAsync() async {
	let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)
	
	guard let (data, _) = try? await URLSession.shared.data(for: request) else {
		return
	}
	
	let provider = CGDataProvider(data: data as CFData)!
	self.cgImage = CGImage(
		pngDataProviderSource: provider,
		decode: nil,
		shouldInterpolate: false,
		intent: .defaultIntent
	)
}
```

`URLSession` has an async version of `dataTask` we can use here which makes that pretty straightforward. In stark contrast to the GCD-based version, this executes linearly from top to bottom. And while that part is definitely nicer, there’s an important detail that’s now harder to figure out.

What thread is all this running on?

## Isolation

When you look at the GCD version, there’s really just two states. We are either running code on the main thread (queue) or we are not. This arrangement is quite common for application developers. I think this is wonderful, because it is simple and also often sufficient. Lots of apps will never need a more complex model.

We’re going to use the same idea in the concurrency world. Except we have to learn a tiny bit of terminology, because Swift concurrency doesn’t work with threads or queues directly. Instead, it is built up around this concept of isolation.

But I want to stress that it is **not critical** you understand how isolation works.

Before, we had “main thread or not”. The main thread isn’t going anywhere! We’re just going to talk about it terms of `MainActor` or not. That’s it.

Actors are the thing that enforce isolation. The `MainActor` protects it mutable state by “isolating” it to the main thread. When we say code is running “on the MainActor” it will be running on the main thread. Not on the `MainActor` means on some other thread.

(There’s a lot more to isolation than just this. So if you want to go [deeper](/intro-to-isolation) or build up more [intuition](/isolation-intuition), go for it. But, that is definitely not necessary right now.)

## So what’s on the `MainActor`?

Armed with this new terminology, we want to understand what is and is not on the `MainActor`. We can get the information we need from the function definition.

Except this is it and there’s nothing special.

```swift
private func loadImageAsync() async
```

Here’s the plot-twist. If you option-click on `loadImageAsync` in Xcode, you see something different!

```swift
// Xcode popup
@MainActor
private func loadImageAsync() async
```

(Xcode actually does not include the `private` visibility modifier for some reason, but I did just to make the important stuff stand out.)

A `@MainActor` has somehow appeared! But **why**? This, again, comes down to definitions. In this case, it’s the definition of this method’s containing type `RobotView`. The `MainActor` shows up because the type conforms to SwiftUI’s `View`. The process of the `MainActor` propagating through the structure of a type is called “actor inference”.

You can trace it back the whole way by looking at definitions. Or you use this Xcode tool. Or, you can just remember that any time you make a view, all this stuff here is going to be `MainActor`.

```swift
struct AnyViewYouMake: View {
	// everything here will be MainActor automatically
}
```

And if you get unsure, it is completely harmless to add a `@MainActor` yourself. Just maybe redundant.

## So what’s **not** on the `MainActor`?

That was a lot, so let’s take stock of where we are. We know `MainActor` means main thread. And we know `loadImageAsync` is implicitly `MainActor` because it is defined within a `View` conformance. But, that annotation applies to the function as a whole. Does this mean the entire thing is going to run on the main thread?

As a matter of fact, **it does**!

Isolation applies to an entire function. Not some parts - the whole thing. But, I do want to zoom in on one specific bit. This does **not** mean the networking request is going to happen on the main thread.

```swift
private func loadImageAsync() async {
	// on the MainActor...

	guard let (data, _) = try? await URLSession.shared.data(for: request) else {
		return
	}

	// ... and on the MainActor here too
}
```

See that `await` keyword in there? It’s **important**. Right there, it will become `URLSession.data(for:)`’s definition that decides what isolation will be in effect. This call will **unblock** the `MainActor` and free it up to do other work. Only once a response is available will the function be restarted, again on the `MainActor`.

What you need to know is the function **you** are writing is `MainActor`. You are in charge here, but you are not in charge of how `URLSession.data(for:)` works.

This is radically different from how calling functions usually works, so it’s worth taking a moment to think about.

## Back to the async function

Let’s get back to the problem at hand. Here are some comments to help you follow along.

```swift
// actually MainActor because we're using View
private func loadImageAsync() async {
	// MainActor here
	let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)
	
	// this call might switch to something else,
	// that's up to URLSession
	guard let (data, _) = try? await URLSession.shared.data(for: request) else {
		return
	}
	
	// back on the MainActor now
	
	let provider = CGDataProvider(data: data as CFData)!
	self.cgImage = CGImage(
		pngDataProviderSource: provider,
		decode: nil,
		shouldInterpolate: false,
		intent: .defaultIntent
	)
}
```

It looks like we have a pretty similar solution to our original GCD-based implementation. All of our work is happening on the ~main thread~ `MainActor` except for the network request.

Let’s improve that!

## Nonisolated

What we want is to do only the **essential** work on the `MainActor` and move everything else to the background. So far, we’ve chased down how our the `loadImageAsync` function is `MainActor`. But, we want something that is definitely **not** `MainActor`.

There is a tool to do this: the `nonisolated` keyword.

What `nonisolated` does is **stop** any actor inference and ensure that there will not be any isolation for a function. No isolation means no `MainActor` and that means background thread. Let’s adjust our function to use it, without changing anything else.

```swift
private nonisolated func loadImageAsync() async {
	let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)
	
	guard let (data, _) = try? await URLSession.shared.data(for: request) else {
		return
	}
	
	let provider = CGDataProvider(data: data as CFData)!

	// ERROR: Main actor-isolated property 'cgImage' can not be mutated from a nonisolated context
	self.cgImage = CGImage(
		pngDataProviderSource: provider,
		decode: nil,
		shouldInterpolate: false,
		intent: .defaultIntent
	)
}
```

Ah ha, but the compiler doesn’t like this!

> Main actor-isolated property ‘cgImage’ can not be mutated from a nonisolated context

We’ve now made a function that is guaranteed to not be on the `MainActor`, but we’re trying to access our UI state. This is essentially the same problem we introduced with our incorrect GCD-based system above. It just produces a different error here.

We can definitely fix this. And, the fix is going to be (kinda) similar too!

First, let’s change the function signature. Instead of doing the request and mutation, let’s just produce the image.

```swift
private nonisolated func loadImageAsync() async -> CGImage? {
	let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)
	
	guard let (data, _) = try? await URLSession.shared.data(for: request) else {
		return nil
	}
	
	let provider = CGDataProvider(data: data as CFData)!

	return CGImage(
		pngDataProviderSource: provider,
		decode: nil,
		shouldInterpolate: false,
		intent: .defaultIntent
	)
}
```

This works because we’ve removed the invalid access of the `MainActor`-only `cgImage`. It’s subtle, but when you think about this, this function was doing two very distinct things. A more explicit name could have been `loadImageAndUpdateUI`. Tiny digression, but food for thought.

Anyways now we have to adjust the call site.

```swift
struct RobotView: View {
	@State private var cgImage: CGImage?
	
	var body: some View {
		LoadedImageView(cgImage: cgImage)
			.task {
				self.cgImage = await loadImageAsync()
			}
	}
}
```

Now, we’re taking the image that results from our background request and assigning it. Easy?

## What’s going on in that `task`?

This does work. But, the reason **why** it works is actually kinda tricky. We **know** that the body of that `task` must be `MainActor` because we’re allowed to touch `MainActor` state. But where does that come from?

Let’s use that option-click trick again, first on `body`.

```swift
// Xcode popup
@MainActor
var body: some View { get }
```

This makes sense right? This `body` definition is within the `View` conformance of our type. It’s just following the same rule we learned above. But there’s actually more than actor inference going on here. This is another one of those isolation rules that you do not need to understand right now.

(But you [can](/isolation-intuition), if you want!)

All you need to know is the closure of `task` is going to match the function that called it. `MainActor` on the outside means `MainActor` on the inside.

And I really want to highlight, again, that the `task` being `MainActor` has **no effect** whatsoever on how `loadImageAsync` is executed. It’s definition has `nonisolated` and definitions are what matter.

## Is `nonisolated` safe?

We need to take just a moment to talk about `nonisolated` more.

It is extremely common for people to see the word `nonisolated` and think “unsafe”. But, the `nonisolated` keyword just controls how actor inference works. The compiler will not allow you to introduce any unsafety. And if you don’t believe that for some reason, try it! Like we just saw, you cannot read or write values that need isolation from a non-isolated function. There are even strict rules about what you can get into and out of a non-isolated function. The language as a whole works to implement the data race safety feature of Swift.

(Now, there **is** a variant called `nonisolated(unsafe)` that let’s you opt-out of the compile-time safety. But, you cannot apply that to functions.)

(Also, the compiler is damn smart. There are some places where it allows you to “cheat” because it’s really convenient and it can prove that safety can still be guaranteed.)

Rest assured, `nonisolated` is not just handy, but safe as well.

## Alternative 1: Tasks

There are (at least) two other options that could be used to implement this network request. I want to show you both so you can understand why I didn’t pick them.

Here’s a really common pattern I see all the time.

```swift
private func loadImage() {
	Task.detached {
		let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)
	
		guard let (data, _) = try? await URLSession.shared.data(for: request) else {
			return
		}

		let provider = CGDataProvider(data: data as CFData)!
		
		let image = CGImage(
			pngDataProviderSource: provider,
			decode: nil,
			shouldInterpolate: false,
			intent: .defaultIntent
		)
		
		Task { @MainActor in
			self.cgImage = image
		}
	}
}
```

This is kind of like a direct translation of the GCD-based version. Normally, a `Task` will use the same isolation as the enclosing function. Just like what was going on with the `.task` modifier above. But, `.detached` changes this behavior, which gives us the background thread we need. And then, a **new** `Task` is set up that gets back onto the `MainActor` to update the UI state.

It’s pretty complicated.

One problem is `Task.detached` actually does more than just ignore the enclosing isolation. It isn’t critical you know all the [details](https://developer.apple.com/documentation/swift/task/detached(priority:operation:)-1g00u), but I consider it quite an advanced tool. But, I’ll admit it does get the job done. And, it’s probably appealing because this almost perfectly matches the more-familiar patterns from GCD.

What I **really** don’t like about this version is at the end of this `loadImage` function, the work **hasn’t** finished yet. The `async`/`await` programming model allows you to write code that executes from top-to-bottom, but this is still going outer-to-inner. We **can** fix this by awaiting the tasks. But it’s really just adding a bunch of code and nesting.

All in all, I think this is just an awkward pattern you should avoid.

## Alternative 2: `MainActor.run`

Now, here’s a variant that improves on that a fair bit.

```swift
private nonisolated func loadImage() async {
	let request = URLRequest(url: URL(string: "https://robohash.org/hash-this-text.png")!)

	guard let (data, _) = try? await URLSession.shared.data(for: request) else {
		return
	}

	let provider = CGDataProvider(data: data as CFData)!

	let image = CGImage(
		pngDataProviderSource: provider,
		decode: nil,
		shouldInterpolate: false,
		intent: .defaultIntent
	)

	await MainActor.run {
		self.cgImage = image
	}
}
```

We’re back to expressing our need for a background thread in the function signature. That cuts down on a lot of noise. But, instead of returning the `image`, we are using a new tool to do the assignment in the function. This is much nicer!

But there is a downside. That `MainActor.run` is cool, because it gives us a way to hop onto the right actor and do some work. Except, if you remember, that’s exactly what the `await` keyword is for! When you first start working with concurrency, you may think to yourself “oh I like this because it is explicit”.

In this example, we’re working with a property. Unfortunately, properties are a little quirky in this respect. But, imagine if instead we had a little helper function.

```swift
@MainActor // or possibly through inference
func updateImage(_ image: CGImage?) {
	// ...
}
```

This function needs to manipulate some UI state, so it would be `MainActor`. And that means:

We started here…

```swift
await MainActor.run {
	self.cgImage = image
}
```

… but we could use the function instead…

```swift
await MainActor.run {
	updateImage(image)
}
```

… and that is actually completely equivalent to this!

```swift
await updateImage(image)
```

There’s no need for the `MainActor.run` because the compiler **knows** that `updateImage` is `MainActor`. And this is the main thing I don’t love about `MainActor.run`. It isn’t always even obvious when you need it! Don’t forget, concurrency is part of the type system.

## We made it

Whew. This turned out to be a lot longer than I expected when starting. I really appreciate you making your way through, and I hope it was helpful. We did have to skip some details on how isolation works. But, I honestly think that’s good! Start with the basics of understanding when things are and are not going to run on the main thread. That will get you really far!

If you want to start digging into some more details, I have a bunch of other things written up that covers some of the things we skipped.

*   [An Introduction to Isolation in Swift](/intro-to-isolation)
*   [Swift Isolation Intuition](/isolation-intuition)
*   [Is Dynamic Isolation Bad?](/dynamic-isolation)

But, I really do recommend you to focus on the **basics** first. Starting with a solid foundation is going to help keep frustration to a minimum.

There’s also now [second installment](/step-by-step-reading-from-storage) of this series, if you want to keep going!

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.
