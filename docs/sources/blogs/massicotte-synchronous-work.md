# Synchronous Work
Mar 3, 2025

Occasionally, you’ll come across something that will really influence your thinking on a topic. This happened to me after reading a [post](https://forums.swift.org/t/pitch-inherit-isolation-by-default-for-async-functions/74862/99) on the Swift forums. That was nearly 6 months ago as I write, but I’m still thinking about it today.

How should we approach synchronous work?

## Maybe it’s fast?

Everyone is really worried about blocking the main thread. And for very good reason! You want to keep your app responsive. To do that you must make sure you aren’t tying it up the main thread for too long.

This might sound obvious, but for this to happen the work has to be **both** long-running **and** synchronous.

If the work is not long-running, it just doesn’t matter. In fact, shifting very small amounts of work off the main thread can actually be **bad** for performance. This is because, while the cost is tiny, it is not free to switch to/from a thread.

```swift
DispatchQueue.global().async {
	// uh-oh better do this off the main thread!!!!
	let result = x * y

	DispatchQueue.main.async {
		// ... and now publish the result
		self.state = result
	}
}
```

This is inefficient. The cost of switching away and then back to the main thread is significantly higher than a single multiplication. Practically speaking, this kind of stuff doesn’t really matter unless you do it a lot. But, efficiency aside, you **definitely** do now have a lot more complexity.

Here, you may have to handle this weird in-between situation where work is in-progress but not yet complete. And even if that doesn’t matter in this specific case, every reader of this code now needs to at least **think** about it.

The point is, adding concurrency (lowercase-c) to your code comes with increased complexity in multiple dimensions. And that increase can be **substantial**.

## Maybe it’s slow?

You should start with a reasonable expectation that the work you are dealing with will be slow. Even if only sometimes! Because otherwise paying the efficiency and complexity cost is totally not worth it.

There are lots of familiar examples that do fit this pattern. Like everyone’s favorite, decoding JSON.

```swift
let model = try JSONDecoder().decode(MyModel.self, from: data)
```

The input, that `data` here, can be arbitrarily large. That might not be typical, but it is absolutely possible. The cost of this decoding could be a real problem and it is totally justified to want this off the main thread.

So, how should we do that?

The classic pattern you’ll see when using dispatch looks just like what we did with that silly multiplication above.

```swift
DispatchQueue.global().async {
	let model = try JSONDecoder().decode(MyModel.self, from: data)
	
	DispatchQueue.main.async {
		// do something with model
	}
}
```

You first get yourself off the current queue so you can do the expensive work without blocking. And then, you return to some known queue to make the completed results available. Pretty straightforward.

(As it turns out, this exact pattern is often not the [best approach](https://forums.developer.apple.com/forums/thread/711736), but it’s fine for our discussion.)

If we want to use `async`/`await` for this, we have a number of options.

(Performance side-note: I think that Swift Concurrency is [ideally-suited](https://forums.swift.org/t/pitch-inherit-isolation-by-default-for-async-functions/74862/52) for CPU-bound work. It’s easy to keep the system maximally busy without needing to worry about thread explosion.)

### Task.detached

It’s really common to see people reach for `Task.detached` when trying to handle stuff like this.

```swift
Task.detached {
	let model = try JSONDecoder().decode(MyModel.self, from: data)
	
	Task { @MainActor in
		// do something with model
	}
}
```

While it **does** give you a place to run code without blocking the enclosing actor, it has a whole bunch of other [side-effects](https://developer.apple.com/documentation/swift/task/detached(priority:operation:)-1g00u) you probably don’t want. It’s very understandable that `Task.detached` is used like this, but I think you should pretty much never do it.

There are just better tools for this job.

### non-isolated + async

An option I **do** like is to use a non-isolated async function. Non-isolated async functions will **always**\* execute on the “global executor”, which is guaranteed to not be on any actor. This gives you an easy way to prevent code from blocking the `MainActor` (or any other).

```swift
nonisolated func decodeModel(from data: Data) async throws -> MyModel {
	try JSONDecoder().decode(MyModel.self, from: data)
}
```

A function like this will never block the caller. In fact, callers don’t even have to think about, or even know, it could be slow. All they need to know is it is asynchronous.

(* [today](https://forums.swift.org/t/se-0461-run-nonisolated-async-functions-on-the-callers-actor-by-default/77987), anyways. But this is how you should be thinking about it until things change.)

## Why do this at all?

This brings up an interesting question.

If JSON decoding can be slow and the language provides a way to guarantee background execution via a function signature, why doesn’t `JSONDecoder.decode` just work that way? If the standard library were changed such that `JSONDecoder.decode` became async, all this would just magically work. It’s tempting!

But, I think it is **never** the right choice for potentially-slow operations.

## Synchronous is strictly more useful

If `JSONDecoder.decode` became async, it’s true that it would completely eliminate the possibly of blocking an actor. That’s good! But, it comes with an enormous trade-off.

What if you actually **want** to block?

This is not pretend. It can useful for testing. It can be useful for doing work atomically. It can be called from both synchronous and asynchronous contexts. A synchronous function is just **more** flexible. Yes, it’s true that sometimes, maybe even most of the time, callers don’t want to block.

Synchronous functions just give callers more options.

## async let

Ok, so I hope that I have convinced you that synchronous functions are useful. But they are also more work when you want them to not block. And that’s most of the time.

Luckily, there’s another option that I haven’t used much **yet**, but which is rapidly becoming my favorite. It’s `async let`!

```swift
async let model = try JSONDecoder().decode(MyModel.self, from: data)

// this will suspend the caller until the work is complete
await model
```

I think it’s super cool that `async let` gives you this really lightweight way to spin up a task and run some code. It can even be used for functions that have no return value.

But, there is a little subtly here.

```swift
async let _ = // what's actually happening here?
```

The whole purpose of an `async let` is to allow some work to begin **without** stopping execution. The right hand side of this expression is synchronous.

Because `JSONDecoder.decode` is non-isolated, this async let will shift that work off the current actor. It will then run in the same context that non-isolated async work runs - on the global executor.

But you cannot get around the isolation rules with this.

```swift
@MainActor
class MyClass {
	func doStuff() async {
		async let value = expensive()

		print(await value)
	}

	func expensive() -> Int {
		// let's just pretend this is slow
	}
}
```

In this example, `expensive` is a member of a `MainActor`-isolated type. So, even though `expensive` is being called via `async let`, it will still end up running on the main thread. To make this non-blocking, you need the function to be non-isolated, like this:

```swift
nonisolated func expensive() -> Int {
}
```

## Asynchronous work

Remember, we are worried about work that is **both** long-running and synchronous. So far, we’ve talked a lot about how to manage synchronous work. But, what about asynchronous stuff?

By definition, awaiting an async function call will free up the current actor until that call completes. So the short answer is once you see an “await”, you have nothing to worry about.

But there is a long answer. To understand it all, we have to look more closely at how async functions actually work.

```swift
@MainActor
func callee() async {
	print("B")
	print("C")
}

@MainActor
func caller() async {
	print("A")

	await callee()

	print("D")
}
```

These two functions might look too simplistic to be useful but we can learn a lot from them! If you run `caller`, the output will look like this:

```
A
B
C
D
```

This output, however, doesn’t give us the whole story. There’s an important question: can there ever be a suspension between A/B or C/D?

The `await` keyword marks suspension points. These are spots where the current task can suspend and/or isolation can change. But, those things might not happen! These are really **potential** suspension points.

It is semantic **guarantee** that when entering or exiting an async function **with the same isolation**, no suspension will occur. That last bit is really important. This only holds when isolation does not change.

But what this means is, despite `callee` being an async function, there will not be any suspensions at all. We’ll go from “A” all the way to “D” completely synchronously.

(There are situations where this fact is critical for correct operation. But, here we just want to use it to explore potential blocking.)

## Wait wait wait

This is kind of bad news right? I just told you that once you see an `await` you don’t have to worry. Then I followed that up by explaining that even a call with `await` could actually be synchronous. We know that synchronous calls can be a problem.

Let’s expand our example just slightly so we can investigate.

```swift
@MainActor
func callee() async {
	print("B")
	
	// this is a problem!
	slowSynchronousWork()
	
	print("C")
}

@MainActor
func caller() async {
	print("A")

	await callee()

	print("D")
}
```

I’ve introduced a slow, synchronous call into `callee`. So now, the output will look like this:

```
A
B
*long delay*
C
D
```

Synchronous and slow! This exactly what we want to avoid!

## What do we do?

Now, it could be that `callee` is just implemented inefficiently. It is the thing making that call to `slowSynchronousWork` after all. Maybe it should be using an `async let` or some other mechanism to avoid blocking.

The only reason that even matters at all is because of `callee`’s **isolation**. If it were non-isolated, things would be fine. It many cases, it might not even need to be non-isolated, just as long as it is **not** `MainActor`.

And here’s the critical thing.

In **both** of these situations, the problem can only be solved by `callee`. Addressing any problematic blocking here really comes down to thinking about and changing the isolation involved. The `caller` function really has no control over that.

## Asynchronous Thinking

I think the way to approach this is purely in terms of synchronous vs asynchronous execution. If you are writing a synchronous function that could be slow, think about making it non-isolated. You will, of course, need to pass arguments in and get results back out. That may require `Sendable` types or `sending`. But this is always the case when moving data around across isolation.

If you are writing an asynchronous function, just focus on getting your problem solved. You might find a **synchronous** bottleneck, but you can address that without breaking your API contract. Don’t stress out about the performance of calls you make with `await`.

But if you happen to encounter the situation where you are a) calling an async function b) with the same isolation and c) that is then hitting a synchronous bottleneck, you have yourself a deeper issue. You almost certainly need to make some isolation changes. And if you aren’t in control of that function I’d like you to tell about what you did, because I’m very interested!

---

[Sponsorship](https://github.com/sponsors/mattmassicotte) helps me do my writing. I also do consulting, training, and run workshops specifically for Swift concurrency. [Get in touch](/about) if you think I could help.

***

massicotte.org

I write stuff here.

*   [Mastodon](https://mastodon.social/@mattiem)
*   [GitHub](https://github.com/mattmassicotte)
*   [Bluesky](https://bsky.app/profile/massicotte.org)
*   [LinkedIn](https://www.linkedin.com/in/mattmassicotte/)
*   [RSS](https://www.massicotte.org/feed.xml)
